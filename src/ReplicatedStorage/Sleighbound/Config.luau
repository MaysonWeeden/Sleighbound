--!strict
-- Sleighbound shared tuning. Every number the movement feel and squad rules depend on lives here.
return {
	WallTag = "WallRun", -- CollectionService tag: surfaces you can wall run / climb

	Squad = {
		MaxMembers = 4,
		InviteTimeout = 30, -- seconds an invite stays valid
		ActionCooldown = 0.15, -- per-player rate limit on squad actions
	},

	Move = {
		WalkSpeed = 16,
		SprintSpeed = 26,
		SprintRamp = 0.3, -- seconds to reach full sprint

		JumpPower = 50,
		AirJumps = 1, -- extra jumps in the air (double jump)
		DoubleJumpPower = 50,
		CoyoteTime = 0.12, -- seconds after leaving a ledge you can still jump
		JumpBuffer = 0.1, -- seconds before landing a jump press is remembered

		SlideMinSpeed = 18,
		SlideBoost = 1.15,
		SlideDuration = 0.8,
		SlideCooldown = 1.0,
		SlideEndSpeed = 14,
		SlideHipHeight = 0.3,

		WallRunMinSpeed = 14,
		WallRunSpeed = 24,
		WallRunTime = 1.8,
		WallRayDistance = 3.4,
		WallRunCooldown = 0.35,
		WallKickSpeed = 38,
		WallKickUp = 46,

		ClimbSpeed = 16,
		ClimbTime = 0.9,

		BaseFOV = 70,
		MaxFOV = 82,
		FOVStartSpeed = 18,
		FOVMaxSpeed = 40,
	},
}
