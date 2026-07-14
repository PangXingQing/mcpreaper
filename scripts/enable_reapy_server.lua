reaper.PreventUIRefresh(1)

reaper.ClearConsole()

local _, _, sectionId = reaper.get_config_var_string("csurf", "")

local found = false
for i = 0, 100 do
    local _, _, mode, port, path = reaper.get_config_var_string("csurf_" .. i, "")
    if mode == "HTTP" and port == "2307" then
        found = true
        break
    end
end

if not found then
    reaper.set_config_var_string("csurf_" .. sectionId, "HTTP 0 2307 '' 'index.html' 0 ''")
    reaper.ShowConsoleMsg("Web interface on port 2307 enabled.\n")
else
    reaper.ShowConsoleMsg("Web interface on port 2307 already exists.\n")
end

local f = io.open(reaper.GetResourcePath() .. "/enable_distant_api.txt", "w")
if f then
    f:write("1")
    f:close()
    reaper.ShowConsoleMsg("enable_distant_api.txt created.\n")
end

reaper.PreventUIRefresh(-1)

reaper.ShowMessageBox("Reapy distant API enabled!\n\nYou can now connect to REAPER from external Python scripts.", "Success", 0)