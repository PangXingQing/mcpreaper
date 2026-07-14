reaper.PreventUIRefresh(1)
reaper.ClearConsole()

local function log(msg)
    reaper.ShowConsoleMsg(msg .. "\n")
end

-- Persist reapy port so external clients can reconnect after REAPER restarts.
reaper.SetExtState("reapy", "server_port", "2306", true)

local action_key = reaper.GetExtState("reapy", "activate_reapy_server")
if action_key == "" then
    reaper.PreventUIRefresh(-1)
    reaper.ShowMessageBox(
        "Missing reapy activation action key.\n\nRun enable_reapy_server.lua once first.",
        "Reapy Setup Required",
        0
    )
    return
end

local command_id = reaper.NamedCommandLookup(action_key)
if command_id == 0 then
    reaper.PreventUIRefresh(-1)
    reaper.ShowMessageBox(
        "Cannot resolve reapy activation action id: " .. action_key .. "\n\nRe-run enable_reapy_server.lua.",
        "Reapy Setup Required",
        0
    )
    return
end

reaper.Main_OnCommand(command_id, 0)

local port = reaper.GetExtState("reapy", "server_port")
reaper.PreventUIRefresh(-1)

if port == "2306" then
    log("reapy server port fixed to 127.0.0.1:2306")
    reaper.ShowMessageBox(
        "Reapy startup binding configured.\n\nTarget: 127.0.0.1:2306",
        "Success",
        0
    )
else
    log("reapy server_port is currently: " .. port)
    reaper.ShowMessageBox(
        "Reapy activation executed, but server_port is not 2306.\nCurrent value: " .. port,
        "Warning",
        0
    )
end
