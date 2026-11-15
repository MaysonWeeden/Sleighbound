-- Theme: every colour and font the UI and the menu scene use. Add a theme here and it appears in Settings.
local Theme = {}

Theme.order = { "Candy", "Frost" }

Theme.themes = {
	Candy = {
		Name = "Candy",
		-- UI
		Bg = Color3.fromRGB(28, 14, 60),
		Panel = Color3.fromRGB(58, 30, 112),
		PanelDark = Color3.fromRGB(36, 18, 78),
		Primary = Color3.fromRGB(238, 60, 90),
		Secondary = Color3.fromRGB(70, 214, 176),
		Gold = Color3.fromRGB(255, 200, 64),
		Pink = Color3.fromRGB(255, 130, 196),
		Good = Color3.fromRGB(80, 220, 130),
		Bad = Color3.fromRGB(240, 80, 80),
		Text = Color3.fromRGB(255, 255, 255),
		TextDim = Color3.fromRGB(205, 190, 240),
		Outline = Color3.fromRGB(26, 10, 52),
		TitleTop = Color3.fromRGB(255, 232, 120),
		TitleBottom = Color3.fromRGB(255, 120, 190),
		Font = Enum.Font.FredokaOne,
		TitleFont = Enum.Font.LuckiestGuy,
		-- menu scene
		Ground = Color3.fromRGB(238, 246, 255),
		Houses = {
			Color3.fromRGB(255, 120, 150), Color3.fromRGB(110, 225, 190), Color3.fromRGB(255, 205, 90),
			Color3.fromRGB(150, 140, 255), Color3.fromRGB(255, 160, 90),
		},
		Roof = Color3.fromRGB(190, 40, 70),
		Tree = Color3.fromRGB(40, 150, 90),
		Lights = { Color3.fromRGB(255, 80, 100), Color3.fromRGB(90, 240, 200), Color3.fromRGB(255, 220, 90), Color3.fromRGB(150, 150, 255) },
		ClockTime = 21.5,
	},

	Frost = {
		Name = "Frost",
		Bg = Color3.fromRGB(10, 26, 56),
		Panel = Color3.fromRGB(22, 56, 110),
		PanelDark = Color3.fromRGB(12, 34, 76),
		Primary = Color3.fromRGB(70, 160, 255),
		Secondary = Color3.fromRGB(120, 235, 240),
		Gold = Color3.fromRGB(255, 232, 150),
		Pink = Color3.fromRGB(190, 170, 255),
		Good = Color3.fromRGB(100, 235, 170),
		Bad = Color3.fromRGB(255, 110, 120),
		Text = Color3.fromRGB(255, 255, 255),
		TextDim = Color3.fromRGB(180, 210, 245),
		Outline = Color3.fromRGB(6, 16, 40),
		TitleTop = Color3.fromRGB(235, 250, 255),
		TitleBottom = Color3.fromRGB(110, 190, 255),
		Font = Enum.Font.FredokaOne,
		TitleFont = Enum.Font.LuckiestGuy,
		Ground = Color3.fromRGB(225, 238, 252),
		Houses = {
			Color3.fromRGB(120, 170, 240), Color3.fromRGB(150, 220, 235), Color3.fromRGB(200, 190, 250),
			Color3.fromRGB(240, 245, 255), Color3.fromRGB(110, 140, 210),
		},
		Roof = Color3.fromRGB(50, 80, 150),
		Tree = Color3.fromRGB(40, 120, 110),
		Lights = { Color3.fromRGB(120, 200, 255), Color3.fromRGB(220, 240, 255), Color3.fromRGB(170, 150, 255) },
		ClockTime = 23,
	},
}

Theme.Current = Theme.themes.Candy

function Theme.set(name)
	local t = Theme.themes[name]
	if t then
		Theme.Current = t
		return true
	end
	return false
end

function Theme.next()
	local idx = table.find(Theme.order, Theme.Current.Name) or 1
	return Theme.order[idx % #Theme.order + 1]
end

return Theme
