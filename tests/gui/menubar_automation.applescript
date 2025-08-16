-- AppleScript helpers for Impetus menu bar app UI testing
-- Functions are invoked via: osascript menubar_automation.applescript <command> [args]

on run argv
  if (count of argv) is 0 then return "usage: osascript menubar_automation.applescript <open|exists|click|nestedclick|screenshot|quit> [args]"
  set cmd to item 1 of argv
  if cmd is "open" then
    return my open_menu()
  else if cmd is "exists" then
    if (count of argv) < 2 then return "missing menu item name"
    set itemName to item 2 of argv
    return my exists_menu_item(itemName)
  else if cmd is "click" then
    if (count of argv) < 2 then return "missing menu item name"
    set itemName to item 2 of argv
    return my click_menu_item(itemName)
  else if cmd is "nestedclick" then
    if (count of argv) < 3 then return "missing parent and child menu names"
    set parentName to item 2 of argv
    set childName to item 3 of argv
    return my click_nested_menu_item(parentName, childName)
  else if cmd is "screenshot" then
    if (count of argv) < 2 then return "missing file path"
    set outPath to item 2 of argv
    do shell script "/usr/sbin/screencapture -x " & quoted form of outPath
    return outPath
  else if cmd is "quit" then
    return my choose_quit()
  else
    return "unknown command: " & cmd
  end if
end run

on get_status_menu_item()
  tell application "System Events"
    tell process "SystemUIServer"
      set theBar to menu bar 1
  set barItems to menu bar items of theBar
  repeat with mi in barItems
        try
          perform action "AXPress" of mi
          delay 1
          if exists menu 1 of mi then
            set m to menu 1 of mi
            if (exists menu item "Open Dashboard" of m) or (exists menu item "Start Server" of m) or (exists menu item "Stop Server" of m) then
              return mi
            else
              tell application "System Events" to key code 53
            end if
          end if
        end try
      end repeat
    end tell
  end tell
  return missing value
end get_status_menu_item

on open_menu()
  repeat with i from 1 to 5
    set mi to my get_status_menu_item()
    if mi is missing value then
      delay 0.5
    else
      return "ok"
    end if
  end repeat
  return "not_found"
end open_menu

on exists_menu_item(itemName)
  set _ to my open_menu()
  set mi to my get_status_menu_item()
  if mi is missing value then return "not_found"
  tell application "System Events"
    tell process "SystemUIServer"
      if exists menu 1 of mi then
        set m to menu 1 of mi
        if exists menu item itemName of m then
          return "ok"
        end if
      end if
    end tell
  end tell
  return "not_found"
end exists_menu_item

on click_menu_item(itemName)
  repeat with i from 1 to 5
    set _ to my open_menu()
    set mi to my get_status_menu_item()
    if mi is not missing value then
      tell application "System Events"
        tell process "SystemUIServer"
          if exists menu 1 of mi then
            set m to menu 1 of mi
            if exists menu item itemName of m then
              click menu item itemName of m
              return "ok"
            end if
          end if
        end tell
      end tell
    end if
    delay 0.5
  end repeat
  return "not_found"
end click_menu_item

on click_nested_menu_item(parentName, childName)
  repeat with i from 1 to 5
    set _ to my open_menu()
    set mi to my get_status_menu_item()
    if mi is not missing value then
      tell application "System Events"
        tell process "SystemUIServer"
          if exists menu 1 of mi then
            set m to menu 1 of mi
            if exists menu item parentName of m then
              click menu item parentName of m
              delay 1
              if exists menu 1 of menu item parentName of m then
                set sm to menu 1 of menu item parentName of m
                if exists menu item childName of sm then
                  click menu item childName of sm
                  return "ok"
                end if
              end if
            end if
          end if
        end tell
      end tell
    end if
    delay 0.5
  end repeat
  return "not_found"
end click_nested_menu_item

on choose_quit()
  set _ to my click_menu_item("Quit Impetus")
  delay 1
  tell application "System Events"
    try
      if exists process "Impetus" then
        tell process "Impetus"
          if exists button "Stop & Quit" of window 1 then click button "Stop & Quit" of window 1
        end tell
      end if
    end try
    try
      if exists process "Python" then
        tell process "Python"
          if exists button "Stop & Quit" of window 1 then click button "Stop & Quit" of window 1
        end tell
      end if
    end try
  end tell
  return "ok"
end choose_quit
