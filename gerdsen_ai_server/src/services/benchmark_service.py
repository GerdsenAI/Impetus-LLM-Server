"""
Model Benchmarking Service
Measures and tracks model performance metrics for optimization
"""

import sqlite3
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime

import psutil
from loguru import logger

from ..config.settings import settings
from ..utils.metal_monitor import metal_monitor


@dataclass
class BenchmarkResult:
    """Single benchmark result"""
    model_id: str
    prompt_length: int
    output_tokens: int
    time_to_first_token_ms: float
    total_time_ms: float
    tokens_per_second: float
    memory_used_gb: float
    gpu_utilization_avg: float
    gpu_memory_used_gb: float
    temperature_celsius: float | None
    timestamp: str
    chip_type: str

    @property
    def tokens_per_second_sustained(self) -> float:
        """Tokens per second excluding first token latency"""
        if self.output_tokens <= 1:
            return 0.0
        time_after_first = self.total_time_ms - self.time_to_first_token_ms
        tokens_after_first = self.output_tokens - 1
        return (tokens_after_first / time_after_first) * 1000 if time_after_first > 0 else 0.0


@dataclass
class BenchmarkSuite:
    """Complete benchmark results for a model"""
    model_id: str
    chip_type: str
    timestamp: str
    results: list[BenchmarkResult]

    @property
    def average_tokens_per_second(self) -> float:
        """Average tokens per second across all tests"""
        return statistics.mean(r.tokens_per_second for r in self.results)

    @property
    def average_first_token_latency_ms(self) -> float:
        """Average time to first token"""
        return statistics.mean(r.time_to_first_token_ms for r in self.results)

    @property
    def peak_tokens_per_second(self) -> float:
        """Best tokens per second achieved"""
        return max(r.tokens_per_second for r in self.results)

    @property
    def average_memory_gb(self) -> float:
        """Average memory usage"""
        return statistics.mean(r.memory_used_gb for r in self.results)


@dataclass
class EmbeddingBenchmarkResult:
    """Single embedding benchmark result"""
    model_name: str
    device: str
    texts_count: int
    dimensions: int
    total_time_ms: float
    per_text_ms: float
    tokens_per_second: float
    timestamp: str


class BenchmarkService:
    """Service for benchmarking model performance"""

    # Standard prompts for benchmarking
    BENCHMARK_PROMPTS = [
        # Short prompt (conversation starter)
        {
            "prompt": "Hello, how are you today?",
            "tokens": 50,
            "category": "short"
        },
        # Medium prompt (typical query)
        {
            "prompt": "Explain the concept of machine learning in simple terms that a high school student could understand. Include examples from everyday life.",
            "tokens": 150,
            "category": "medium"
        },
        # Long prompt (context-heavy)
        {
            "prompt": """You are a helpful AI assistant. Here is some context about Python programming:

Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991. Python's design philosophy emphasizes code readability with its notable use of significant whitespace.

Key features include:
- Dynamic typing and automatic memory management
- Support for multiple programming paradigms
- Extensive standard library
- Large ecosystem of third-party packages

Now, please explain the differences between lists and tuples in Python, when to use each, and provide code examples demonstrating their usage.""",
            "tokens": 200,
            "category": "long"
        },
        # Code generation
        {
            "prompt": "Write a Python function that implements binary search on a sorted list. Include proper error handling and docstring.",
            "tokens": 150,
            "category": "code"
        }
    ]

    def __init__(self):
        self.db_path = settings.model.cache_dir / "benchmarks.db"
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for storing benchmark results"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    prompt_length INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    time_to_first_token_ms REAL NOT NULL,
                    total_time_ms REAL NOT NULL,
                    tokens_per_second REAL NOT NULL,
                    memory_used_gb REAL NOT NULL,
                    gpu_utilization_avg REAL NOT NULL,
                    gpu_memory_used_gb REAL NOT NULL,
                    temperature_celsius REAL,
                    timestamp TEXT NOT NULL,
                    chip_type TEXT NOT NULL,
                    prompt_category TEXT,
                    UNIQUE(model_id, timestamp, prompt_length)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_timestamp
                ON benchmarks(model_id, timestamp DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chip_model
                ON benchmarks(chip_type, model_id)
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS embedding_benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    device TEXT NOT NULL,
                    texts_count INTEGER NOT NULL,
                    dimensions INTEGER NOT NULL,
                    total_time_ms REAL NOT NULL,
                    per_text_ms REAL NOT NULL,
                    tokens_per_second REAL NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)

    def benchmark_model(self, model, model_id: str, chip_type: str,
                       custom_prompts: list[dict] | None = None) -> BenchmarkSuite:
        """Run complete benchmark suite on a model"""
        logger.info(f"Starting benchmark for model: {model_id}")

        prompts = custom_prompts or self.BENCHMARK_PROMPTS
        results = []
        timestamp = datetime.utcnow().isoformat()

        # Warmup run (not recorded)
        logger.info("Running warmup...")
        try:
            model.generate("Hello", max_tokens=10)
        except Exception as e:
            logger.warning(f"Warmup failed: {e}")

        # Run benchmarks
        for i, prompt_config in enumerate(prompts):
            logger.info(f"Running benchmark {i+1}/{len(prompts)}: {prompt_config['category']}")

            try:
                result = self._benchmark_single(
                    model=model,
                    model_id=model_id,
                    prompt=prompt_config['prompt'],
                    max_tokens=prompt_config['tokens'],
                    chip_type=chip_type,
                    timestamp=timestamp
                )

                if result:
                    results.append(result)

                # Cool down between tests
                time.sleep(2)

            except Exception as e:
                logger.error(f"Benchmark failed for prompt {i+1}: {e}")

        if not results:
            raise ValueError("All benchmarks failed")

        suite = BenchmarkSuite(
            model_id=model_id,
            chip_type=chip_type,
            timestamp=timestamp,
            results=results
        )

        # Store results
        self._store_results(results)

        logger.info(f"Benchmark complete: {suite.average_tokens_per_second:.1f} avg tokens/sec")

        return suite

    def _benchmark_single(self, model, model_id: str, prompt: str,
                         max_tokens: int, chip_type: str, timestamp: str) -> BenchmarkResult | None:
        """Run a single benchmark test"""
        # Get initial metrics
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024 ** 3)

        # Start GPU monitoring
        gpu_metrics = []
        if metal_monitor._is_macos():
            metal_monitor.start_monitoring(interval_seconds=0.1)

            def gpu_callback(metrics):
                gpu_metrics.append(metrics)

            metal_monitor.add_callback(gpu_callback)

        try:
            # Tokenize prompt to get length
            prompt_tokens = model.tokenize(prompt) if hasattr(model, 'tokenize') else None
            prompt_length = len(prompt_tokens) if prompt_tokens else len(prompt.split())

            # Time the generation
            start_time = time.perf_counter()
            first_token_time = None
            tokens_generated = 0

            # Use streaming to measure first token latency
            if hasattr(model, 'generate_stream'):
                for i, _token in enumerate(model.generate_stream(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=0.7
                )):
                    if i == 0:
                        first_token_time = time.perf_counter()
                    tokens_generated += 1
            else:
                # Fallback to regular generation
                first_token_time = time.perf_counter()
                response = model.generate(prompt, max_tokens=max_tokens, temperature=0.7)
                tokens_generated = len(model.tokenize(response)) if hasattr(model, 'tokenize') else len(response.split())

            end_time = time.perf_counter()

            # Calculate metrics
            total_time_ms = (end_time - start_time) * 1000
            time_to_first_token_ms = (first_token_time - start_time) * 1000 if first_token_time else 50.0
            tokens_per_second = (tokens_generated / total_time_ms) * 1000 if total_time_ms > 0 else 0

            # Get final memory
            final_memory = process.memory_info().rss / (1024 ** 3)
            memory_used = final_memory - initial_memory

            # Get GPU metrics
            gpu_util_avg = 0.0
            gpu_memory_avg = 0.0
            temperature = None

            if gpu_metrics:
                gpu_util_avg = statistics.mean(m.gpu_utilization for m in gpu_metrics)
                gpu_memory_avg = statistics.mean(m.memory_used_gb for m in gpu_metrics)
                temps = [m.temperature_celsius for m in gpu_metrics if m.temperature_celsius]
                temperature = statistics.mean(temps) if temps else None

            return BenchmarkResult(
                model_id=model_id,
                prompt_length=prompt_length,
                output_tokens=tokens_generated,
                time_to_first_token_ms=time_to_first_token_ms,
                total_time_ms=total_time_ms,
                tokens_per_second=tokens_per_second,
                memory_used_gb=memory_used,
                gpu_utilization_avg=gpu_util_avg,
                gpu_memory_used_gb=gpu_memory_avg,
                temperature_celsius=temperature,
                timestamp=timestamp,
                chip_type=chip_type
            )

        finally:
            # Clean up GPU monitoring
            if metal_monitor._is_macos() and gpu_callback in metal_monitor.callbacks:
                metal_monitor.remove_callback(gpu_callback)

    def _store_results(self, results: list[BenchmarkResult]):
        """Store benchmark results in database"""
        with sqlite3.connect(self.db_path) as conn:
            for result in results:
                data = asdict(result)
                conn.execute("""
                    INSERT OR REPLACE INTO benchmarks
                    (model_id, prompt_length, output_tokens, time_to_first_token_ms,
                     total_time_ms, tokens_per_second, memory_used_gb, gpu_utilization_avg,
                     gpu_memory_used_gb, temperature_celsius, timestamp, chip_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['model_id'], data['prompt_length'], data['output_tokens'],
                    data['time_to_first_token_ms'], data['total_time_ms'],
                    data['tokens_per_second'], data['memory_used_gb'],
                    data['gpu_utilization_avg'], data['gpu_memory_used_gb'],
                    data['temperature_celsius'], data['timestamp'], data['chip_type']
                ))

    def get_model_history(self, model_id: str, limit: int = 10) -> list[BenchmarkSuite]:
        """Get benchmark history for a model"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get unique benchmark runs
            runs = conn.execute("""
                SELECT DISTINCT timestamp, chip_type
                FROM benchmarks
                WHERE model_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (model_id, limit)).fetchall()

            suites = []
            for run in runs:
                # Get all results for this run
                results = conn.execute("""
                    SELECT * FROM benchmarks
                    WHERE model_id = ? AND timestamp = ?
                    ORDER BY prompt_length
                """, (model_id, run['timestamp'])).fetchall()

                benchmark_results = [
                    BenchmarkResult(**dict(r)) for r in results
                ]

                if benchmark_results:
                    suites.append(BenchmarkSuite(
                        model_id=model_id,
                        chip_type=run['chip_type'],
                        timestamp=run['timestamp'],
                        results=benchmark_results
                    ))

            return suites

    def get_chip_comparison(self, model_id: str) -> dict[str, dict]:
        """Compare model performance across different chips"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            results = conn.execute("""
                SELECT
                    chip_type,
                    AVG(tokens_per_second) as avg_tps,
                    MAX(tokens_per_second) as max_tps,
                    AVG(time_to_first_token_ms) as avg_ttft,
                    AVG(memory_used_gb) as avg_memory,
                    AVG(gpu_utilization_avg) as avg_gpu_util,
                    COUNT(DISTINCT timestamp) as run_count
                FROM benchmarks
                WHERE model_id = ?
                GROUP BY chip_type
                ORDER BY avg_tps DESC
            """, (model_id,)).fetchall()

            return {
                row['chip_type']: {
                    'average_tokens_per_second': row['avg_tps'],
                    'peak_tokens_per_second': row['max_tps'],
                    'average_first_token_ms': row['avg_ttft'],
                    'average_memory_gb': row['avg_memory'],
                    'average_gpu_utilization': row['avg_gpu_util'],
                    'benchmark_runs': row['run_count']
                }
                for row in results
            }

    def benchmark_embedding_model(
        self,
        model_name: str,
        sample_texts: list[str] | None = None,
        iterations: int = 10,
    ) -> EmbeddingBenchmarkResult:
        """Benchmark an embedding model via the compute dispatcher.

        Args:
            model_name: Short embedding model name.
            sample_texts: Texts to embed. Defaults to a built-in set.
            iterations: Number of iterations to average over.

        Returns:
            EmbeddingBenchmarkResult with timing data.
        """
        from ..model_loaders.compute_dispatcher import compute_dispatcher

        if sample_texts is None:
            sample_texts = [
                "Hello world",
                "The quick brown fox jumps over the lazy dog.",
                "Machine learning on Apple Silicon provides excellent performance.",
                "Embeddings are useful for semantic search and retrieval augmented generation.",
            ]

        logger.info(f"Benchmarking embedding model '{model_name}' ({iterations} iterations)")

        # Warmup run
        compute_dispatcher.embed(sample_texts[:1], model_name)

        # Timed runs
        times: list[float] = []
        for _ in range(iterations):
            start = time.perf_counter()
            vectors = compute_dispatcher.embed(sample_texts, model_name)
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)

        avg_total = statistics.mean(times)
        avg_per_text = avg_total / len(sample_texts)
        total_tokens = sum(len(t.split()) for t in sample_texts)
        tps = (total_tokens / (avg_total / 1000)) if avg_total > 0 else 0
        dimensions = len(vectors[0]) if vectors else 0
        device = compute_dispatcher.get_active_device()
        timestamp = datetime.utcnow().isoformat()

        result = EmbeddingBenchmarkResult(
            model_name=model_name,
            device=device,
            texts_count=len(sample_texts),
            dimensions=dimensions,
            total_time_ms=round(avg_total, 2),
            per_text_ms=round(avg_per_text, 2),
            tokens_per_second=round(tps, 1),
            timestamp=timestamp,
        )

        # Store
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO embedding_benchmarks
                   (model_name, device, texts_count, dimensions, total_time_ms,
                    per_text_ms, tokens_per_second, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    result.model_name, result.device, result.texts_count,
                    result.dimensions, result.total_time_ms, result.per_text_ms,
                    result.tokens_per_second, result.timestamp,
                ),
            )

        logger.info(
            f"Embedding benchmark: {avg_per_text:.2f}ms/text, "
            f"{tps:.0f} tok/s, device={device}"
        )
        return result

    def get_all_models_summary(self) -> list[dict]:
        """Get summary of all benchmarked models"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            results = conn.execute("""
                SELECT
                    model_id,
                    chip_type,
                    AVG(tokens_per_second) as avg_tps,
                    AVG(time_to_first_token_ms) as avg_ttft,
                    AVG(memory_used_gb) as avg_memory,
                    MAX(timestamp) as latest_run,
                    COUNT(DISTINCT timestamp) as total_runs
                FROM benchmarks
                GROUP BY model_id, chip_type
                ORDER BY avg_tps DESC
            """).fetchall()

            return [dict(row) for row in results]


# Singleton instance
benchmark_service = BenchmarkService()
