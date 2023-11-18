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
	local func, err = load("return " .. message)
	if not func then
		func, err = load(message)
		if not func then return print(err) end
	end
	setfenv(func, StyxScribeREPL.Environment)
	local ret = table.pack(pcall(func))
	if ret.n <= 1 then return end
	if echo then
		print("Out: " .. ModUtil.Args.Map(toString, table.unpack(ret, 2, ret.n)))
	end
	return table.unpack(ret, 2, ret.n)
end

function StyxScribeREPL.RunPython(message)
	print("StyxScribeREPL: " .. message)
end

local function runLua(message)
	return StyxScribeREPL.RunLua(message, false)
end

StyxScribeREPL.Internal = ModUtil.UpValues(function()
	return toString, runLua
end)

StyxScribe.AddHook(runLua, "StyxScribeREPL: ", StyxScribeREPL)
