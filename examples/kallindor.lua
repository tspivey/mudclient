function simple_alias(n, c) alias("^" .. n .. "( .+)?$", function (m) send(c .. m[1]) end) end
function omit(x) trigger(x, nil, {omit=true}) end
function ts(x, y) trigger(x, function () send(y) end) end

simple_alias("m", "c 'magic missile'")
simple_alias("fb", "c fireball")
messages = {}

function add(message)
	table.insert(messages, message)
	if #table > 20 then
		table.remove(messages, 1)
	end
end

function say_message(n)
	if #messages < n then
		output.speak("No message")
		return
	end
	local item = #messages + 1 - n
	output.speak(messages[item])
end

for i = 1, 9 do
	bind("alt+" .. i, function() say_message(i) end)
end

bind("control+r", function ()
	send(world.history[-1])
end)

function addline(m, l) add(l) end

trigger("^(.*?) chats \'(.*?)\'$", addline)
trigger(".+ tells the group '.+'", addline)

-- These are annoying
omit("^A steaming pile of (.*?)'s entrails is lying here\\.$")
omit("^The amputated leg of (.*?) is still attempting to run off\\.$")
omit("^The splattered brains of (.*?) are lying here\\.$")
omit("^The steaming turds of (.*?) assail your nostrils\\.$")
omit("^.+ dodges .+ attack.$")

-- group things I Have to deal with
ts("^(.*?) climbs A ladder\\.$", "climb ladder")
ts("^(.+) steps into A floating palace\\..", "enter palace")
ts("^.+ steps into A cargo ship\\.$", "enter ship")
