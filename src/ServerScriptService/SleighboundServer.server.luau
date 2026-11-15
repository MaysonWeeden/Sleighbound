--!strict
-- SleighboundServer: squads (invite / accept / leave / auto-fill / start) and moving squads between lobby and the run.
-- The server owns all squad state. Clients only send an action name plus one argument, and every argument is validated.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local SB = ReplicatedStorage:WaitForChild("Sleighbound")
local Config = require(SB:WaitForChild("Config"))
local MAX: number = Config.Squad.MaxMembers
local INVITE_TIMEOUT: number = Config.Squad.InviteTimeout
local COOLDOWN: number = Config.Squad.ActionCooldown

local remotes = Instance.new("Folder")
remotes.Name = "Remotes"
local stateRemote = Instance.new("RemoteEvent")
stateRemote.Name = "SquadState"
stateRemote.Parent = remotes
local actionRemote = Instance.new("RemoteEvent")
actionRemote.Name = "SquadAction"
actionRemote.Parent = remotes
remotes.Parent = SB

type Squad = {
	id: number,
	host: Player,
	members: { Player },
	autofill: boolean,
	state: string, -- "Lobby" or "InRound"
}
type Invite = { from: Player, t: number }

local squads: { [number]: Squad } = {}
local playerSquad: { [Player]: Squad } = {}
local invites: { [Player]: { [number]: Invite } } = {}
local lastAction: { [Player]: number } = {}
local nextId = 0

---------------------------------------------------------------- squad helpers
local function newSquad(host: Player): Squad
	nextId += 1
	local s: Squad = { id = nextId, host = host, members = { host }, autofill = false, state = "Lobby" }
	squads[s.id] = s
	playerSquad[host] = s
	return s
end

local function removeFromSquad(p: Player)
	local s = playerSquad[p]
	if not s then
		return
	end
	playerSquad[p] = nil
	local i = table.find(s.members, p)
	if i then
		table.remove(s.members, i)
	end
	if #s.members == 0 then
		squads[s.id] = nil
	elseif s.host == p then
		s.host = s.members[1]
	end
end

local function pruneInvites()
	local now = os.clock()
	for p, list in invites do
		for sid, inv in list do
			if now - inv.t > INVITE_TIMEOUT or not squads[sid] or inv.from.Parent == nil then
				list[sid] = nil
			end
		end
		if p.Parent == nil then
			invites[p] = nil
		end
	end
end

local function buildState(p: Player)
	local s = playerSquad[p]
	local members = {}
	if s then
		for _, m in s.members do
			table.insert(members, { userId = m.UserId, name = m.DisplayName, isHost = (m == s.host) })
		end
	end
	local others = {}
	for _, q in Players:GetPlayers() do
		local qs = playerSquad[q]
		if q ~= p and (s == nil or qs ~= s) then
			table.insert(others, { userId = q.UserId, name = q.DisplayName, squadSize = if qs then #qs.members else 1 })
		end
	end
	local inv = {}
	local mine = invites[p]
	if mine then
		for sid, info in mine do
			table.insert(inv, { squadId = sid, fromName = info.from.DisplayName, fromId = info.from.UserId })
		end
	end
	return {
		squadId = if s then s.id else 0,
		hostId = if s then s.host.UserId else 0,
		autofill = if s then s.autofill else false,
		state = if s then s.state else "Lobby",
		maxMembers = MAX,
		members = members,
		others = others,
		invites = inv,
	}
end

local function push(p: Player)
	stateRemote:FireClient(p, buildState(p))
end

local function pushAll()
	pruneInvites()
	for _, p in Players:GetPlayers() do
		push(p)
	end
end

---------------------------------------------------------------- teleports
local function practiceCFrame(index: number): CFrame
	local practice = workspace:FindFirstChild("Practice")
	if practice then
		local spawnPart = practice:FindFirstChild("PracticeSpawn")
		if spawnPart and spawnPart:IsA("BasePart") then
			return spawnPart.CFrame * CFrame.new((index - 2.5) * 4, 3, 0)
		end
	end
	return CFrame.new((index - 2.5) * 4, 10, 0)
end

local function lobbyCFrame(): CFrame
	local lobby = workspace:FindFirstChild("SpawnLocation")
	if lobby and lobby:IsA("BasePart") then
		return lobby.CFrame * CFrame.new(0, 4, 0)
	end
	return CFrame.new(0, 10, 0)
end

local function teleport(p: Player, cf: CFrame)
	local char = p.Character
	if char then
		char:PivotTo(cf)
	end
end

---------------------------------------------------------------- actions
local function startSquad(s: Squad)
	if s.autofill then
		for _, q in Players:GetPlayers() do
			if #s.members >= MAX then
				break
			end
			local qs = playerSquad[q]
			if qs and qs ~= s and #qs.members == 1 and qs.state == "Lobby" then
				removeFromSquad(q)
				table.insert(s.members, q)
				playerSquad[q] = s
			end
		end
	end
	s.state = "InRound"
	for i, m in s.members do
		teleport(m, practiceCFrame(i))
	end
end

local function handle(player: Player, action: string, arg: any)
	local s = playerSquad[player]
	if not s then
		return
	end

	if action == "Sync" then
		push(player)
		return
	end

	if action == "Invite" then
		if typeof(arg) ~= "number" or s.host ~= player or s.state ~= "Lobby" or #s.members >= MAX then
			return
		end
		local target = Players:GetPlayerByUserId(arg)
		if not target or target == player then
			return
		end
		local ts = playerSquad[target]
		if ts == s or (ts and ts.state ~= "Lobby") then
			return
		end
		local list = invites[target]
		if not list then
			list = {}
			invites[target] = list
		end
		local count = 0
		for _ in list do
			count += 1
		end
		if count >= 5 and not list[s.id] then
			return
		end
		list[s.id] = { from = player, t = os.clock() }
		pushAll()
		task.delay(INVITE_TIMEOUT + 0.2, pushAll)
	elseif action == "Accept" then
		if typeof(arg) ~= "number" or s.state ~= "Lobby" then
			return
		end
		local list = invites[player]
		local info = list and list[arg]
		local target = squads[arg]
		if not info or not target or target.state ~= "Lobby" or #target.members >= MAX or target == s then
			return
		end
		removeFromSquad(player)
		table.insert(target.members, player)
		playerSquad[player] = target
		invites[player] = nil
		pushAll()
	elseif action == "Decline" then
		if typeof(arg) ~= "number" then
			return
		end
		local list = invites[player]
		if list then
			list[arg] = nil
		end
		push(player)
	elseif action == "Leave" then
		if s.state ~= "Lobby" or #s.members <= 1 then
			return
		end
		removeFromSquad(player)
		newSquad(player)
		pushAll()
	elseif action == "Autofill" then
		if typeof(arg) ~= "boolean" or s.host ~= player or s.state ~= "Lobby" then
			return
		end
		s.autofill = arg
		pushAll()
	elseif action == "Start" then
		if s.host ~= player or s.state ~= "Lobby" then
			return
		end
		startSquad(s)
		pushAll()
	elseif action == "ReturnToLobby" then
		removeFromSquad(player)
		newSquad(player)
		teleport(player, lobbyCFrame())
		pushAll()
	end
end

actionRemote.OnServerEvent:Connect(function(player: Player, action: unknown, arg: unknown)
	if typeof(action) ~= "string" then
		return
	end
	local now = os.clock()
	if action ~= "Sync" and now - (lastAction[player] or 0) < COOLDOWN then
		return
	end
	lastAction[player] = now
	handle(player, action, arg)
end)

---------------------------------------------------------------- players
local function onPlayerAdded(p: Player)
	newSquad(p)
	pushAll()
end

Players.PlayerAdded:Connect(onPlayerAdded)
for _, p in Players:GetPlayers() do
	onPlayerAdded(p)
end

Players.PlayerRemoving:Connect(function(p: Player)
	removeFromSquad(p)
	invites[p] = nil
	lastAction[p] = nil
	pushAll()
end)
