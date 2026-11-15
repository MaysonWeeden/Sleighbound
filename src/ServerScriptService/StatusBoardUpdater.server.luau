local RS = game:GetService("ReplicatedStorage")
local folder = RS:WaitForChild("SessionStatus")
local board = workspace:WaitForChild("StatusBoard")
local gui = board:WaitForChild("Board")

local function refresh()
	for _, key in ipairs({"A", "B"}) do
		local label = gui:FindFirstChild(key)
		if label then
			label.Text = "Session " .. key .. ": " .. tostring(folder:GetAttribute(key))
		end
	end
end

for _, key in ipairs({"A", "B"}) do
	folder:GetAttributeChangedSignal(key):Connect(refresh)
end
refresh()
