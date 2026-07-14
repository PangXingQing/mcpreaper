reaper.PreventUIRefresh(1)

reaper.ClearConsole()

local function get_config_string(key)
    -- Different REAPER versions may return the config value at different positions.
    local a, b, c = reaper.get_config_var_string(key, "")
    if type(c) == "string" and c ~= "" then
        return c
    end
    if type(b) == "string" and b ~= "" then
        return b
    end
    if type(a) == "string" and a ~= "" then
        return a
    end
    return ""
end

local csurf_value = get_config_string("csurf")
local sectionId = csurf_value:match("(%d+)$")

local found = false
local web_setup_status = "unknown"
for i = 0, 100 do
    local entry = get_config_string("csurf_" .. i)
    if entry:match("^HTTP%s") and entry:find("2307", 1, true) then
        found = true
        break
    end
end

if not found then
    if not sectionId then
        -- Fallback: find the first empty control-surface slot.
        for i = 0, 100 do
            local entry = get_config_string("csurf_" .. i)
            if entry == "" then
                sectionId = tostring(i)
                break
            end
        end
    end

    if not sectionId then
        reaper.ShowConsoleMsg("Failed to find an available control surface slot.\n")
        reaper.PreventUIRefresh(-1)
        reaper.ShowMessageBox("Failed to enable Reapy distant API: no available control surface slot.", "Error", 0)
        return
    end

    if type(reaper.set_config_var_string) == "function" then
        reaper.set_config_var_string("csurf_" .. sectionId, "HTTP 0 2307 '' 'index.html' 0 ''")
        reaper.ShowConsoleMsg("Web interface on port 2307 enabled.\n")
        web_setup_status = "enabled"
    else
        reaper.ShowConsoleMsg("set_config_var_string is unavailable in this REAPER build.\n")
        reaper.ShowConsoleMsg("Skipped automatic web interface configuration. If 2307 is already accessible, this is fine.\n")
        web_setup_status = "skipped"
    end
else
    reaper.ShowConsoleMsg("Web interface on port 2307 already exists.\n")
    web_setup_status = "exists"
end

local f = io.open(reaper.GetResourcePath() .. "/enable_distant_api.txt", "w")
if f then
    f:write("1")
    f:close()
    reaper.ShowConsoleMsg("enable_distant_api.txt created.\n")
end

-- Persist default distant API port for reapy clients.
reaper.SetExtState("reapy", "server_port", "2306", true)
reaper.ShowConsoleMsg("reapy server_port set to 2306.\n")

reaper.PreventUIRefresh(-1)

if web_setup_status == "skipped" then
    reaper.ShowMessageBox("Reapy distant API enabled.\n\nenable_distant_api.txt was created.\nWeb interface auto-configuration was skipped (API unavailable).\nIf you can open port 2307, no further action is needed.", "Success", 0)
else
    reaper.ShowMessageBox("Reapy distant API enabled!\n\nYou can now connect to REAPER from external Python scripts.", "Success", 0)
end