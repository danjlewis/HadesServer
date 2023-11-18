ModUtil.Mod.Register("StyxScribeREPL")

StyxScribeREPL.Globals = {}
StyxScribeREPL.Environment = setmetatable({}, {
	__index = function(_, k)
		local v = _ENV[k]
		if v ~= nil then return v end
		return StyxScribeREPL.Globals[k]
	end,
	__newindex = function(_, k, v)
		if _ENV[k] ~= nil then
			_ENV[k] = v
			return
		end
		StyxScribeREPL.Globals[k] = v
	end
})

local function toString(obj)
	return ModUtil.ToString.Deep(obj, 500)
end

function StyxScribeREPL.RunLua(message, echo)
	-- modified...
	local uuid = nil
	if message:sub(1, 8) == "Request " then
		message = message:sub(9, #message)

		local i = 1
		while i <= #message do
			local char = message:sub(i, i)
			if char == ":" then
				i = i - 1
				break
			end
			i = i + 1
		end

		uuid = message:sub(1, i)
		message = message:sub(i + 3, #message)
	end
	-- end

	local func, err = load("return " .. message)
	if not func then
		func, err = load(message)
		if not func then return print(err) end
	end
	setfenv(func, StyxScribeREPL.Environment)
	local ret = table.pack(pcall(func))
	if ret.n <= 1 then return end
	if echo then
		-- modified...
		if uuid == nil then
			print("Response: " .. ModUtil.Args.Map(toString, table.unpack(ret, 2, ret.n)))
		else
			print("Response: Request " .. uuid .. ": " .. ModUtil.Args.Map(toString, table.unpack(ret, 2, ret.n)))
		end
		-- end
	end
	return table.unpack(ret, 2, ret.n)
end

function StyxScribeREPL.RunPython(message)
	print("StyxScribeREPL: " .. message)
end

local function runLua(message)
	return StyxScribeREPL.RunLua(message, true)
end

StyxScribeREPL.Internal = ModUtil.UpValues(function()
	return toString, runLua
end)

StyxScribe.AddHook(runLua, "StyxScribeREPL: ", StyxScribeREPL)
