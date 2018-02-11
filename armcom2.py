# -*- coding: UTF-8 -*-
# Python 2.7.14 x64
# Libtcod 1.6.4 x64
##########################################################################################
#                                                                                        #
#                                Armoured Commander II                                   #
#                                                                                        #
##########################################################################################
#             Project Started February 23, 2016; Restarted July 25, 2016                 #
#                           Restarted again January 11, 2018                              #
##########################################################################################
#
#    Copyright (c) 2016-2018 Gregory Adam Scott (sudasana@gmail.com)
#
#    This file is part of Armoured Commander II.
#
#    Armoured Commander II is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Armoured Commander II is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with Armoured Commander II, in the form of a file named "gpl.txt".
#    If not, see <https://www.gnu.org/licenses/>.
#
#    xp_loader.py is covered under a MIT License (MIT) and is Copyright (c) 2015
#    Sean Hagar; see XpLoader_LICENSE.txt for more info.
#
##########################################################################################


##### Libraries #####
import libtcodpy as libtcod				# The Doryen Library
from random import choice, shuffle, sample
from math import floor, cos, sin, sqrt			# math
from math import degrees, atan2, ceil			# heading calculations
import xp_loader, gzip					# loading xp image files
import os, sys, ctypes					# OS-related stuff
import json						# for loading JSON data
import time
from textwrap import wrap				# breaking up strings
import shelve						# saving and loading games

#os.environ['PYSDL2_DLL_PATH'] = os.getcwd() + '/lib'.replace('/', os.sep)
#import sdl2


##########################################################################################
#                                        Constants                                       #
##########################################################################################

# Debug Flags TEMP
AI_SPY = False						# write description of AI actions to console

NAME = 'Armoured Commander II'				# game name
VERSION = '0.1.0-2018-02-06'				# game version in Semantic Versioning format: http://semver.org/
DATAPATH = 'data/'.replace('/', os.sep)			# path to data files
LIMIT_FPS = 50						# maximum screen refreshes per second
WINDOW_WIDTH, WINDOW_HEIGHT = 90, 60			# size of game window in character cells
WINDOW_XM, WINDOW_YM = int(WINDOW_WIDTH/2), int(WINDOW_HEIGHT/2)	# center of game window

# directional and positional constants
DESTHEX = [(0,-1), (1,-1), (1,0), (0,1), (-1,1), (-1,0)]	# change in hx, hy values for hexes in each direction
PLOT_DIR = [(0,-1), (1,-1), (1,1), (0,1), (-1,1), (-1,-1)]	# position of direction indicator
TURRET_CHAR = [254, 47, 92, 254, 47, 92]			# characters to use for turret display

# coordinates for map viewport hexes, radius 6
VP_HEXES = [
	(0,0), (-1,1), (-1,0), (0,-1), (1,-1), (1,0), (0,1), (-2,2), (-2,1), (-2,0), (-1,-1),
	(0,-2), (1,-2), (2,-2), (2,-1), (2,0), (1,1), (0,2), (-1,2), (-3,3), (-3,2), (-3,1),
	(-3,0), (-2,-1), (-1,-2), (0,-3), (1,-3), (2,-3), (3,-3), (3,-2), (3,-1), (3,0),
	(2,1), (1,2), (0,3), (-1,3), (-2,3), (-4,4), (-4,3), (-4,2), (-4,1), (-4,0), (-3,-1),
	(-2,-2), (-1,-3), (0,-4), (1,-4), (2,-4), (3,-4), (4,-4), (4,-3), (4,-2), (4,-1),
	(4,0), (3,1), (2,2), (1,3), (0,4), (-1,4), (-2,4), (-3,4), (-5,5), (-5,4), (-5,3),
	(-5,2), (-5,1), (-5,0), (-4,-1), (-3,-2), (-2,-3), (-1,-4), (0,-5), (1,-5), (2,-5),
	(3,-5), (4,-5), (5,-5), (5,-4), (5,-3), (5,-2), (5,-1), (5,0), (4,1), (3,2), (2,3),
	(1,4), (0,5), (-1,5), (-2,5), (-3,5), (-4,5), (-6,6), (-6,5), (-6,4), (-6,3),
	(-6,2), (-6,1), (-6,0), (-5,-1), (-4,-2), (-3,-3), (-2,-4), (-1,-5), (0,-6), (1,-6),
	(2,-6), (3,-6), (4,-6), (5,-6), (6,-6), (6,-5), (6,-4), (6,-3), (6,-2), (6,-1),
	(6,0), (5,1), (4,2), (3,3), (2,4), (1,5), (0,6), (-1,6), (-2,6), (-3,6), (-4,6), (-5,6)
]

# pre-calculated hexpairs and second hex step for lines of sight along hexspines
HEXSPINES = {
	0: [(0,-1), (1,-1), (1,-2)],
	1: [(1,-1), (1,0), (2,-1)],
	2: [(1,0), (0,1), (1,1)],
	3: [(0,1), (-1,1), (-1,2)],
	4: [(-1,1), (-1,0), (-2,1)],
	5: [(-1,0), (0,-1), (-1,-1)]
}

##### Colour Definitions #####
ELEVATION_SHADE = 0.15					# difference in shading for map hexes of
							#   different elevations
FOV_SHADE = 0.5						# alpha level for FoV mask layer
KEY_COLOR = libtcod.Color(255, 0, 255)			# key color for transparency
PORTRAIT_BG_COL = libtcod.Color(217, 108, 0)		# background color for unit portraits
UNKNOWN_UNIT_COL = libtcod.grey				# unknown enemy unit display colour
ENEMY_UNIT_COL = libtcod.light_red			# known "
DIRT_ROAD_COL = libtcod.Color(50, 40, 25)		# background color for dirt roads

# hex terrain types
HEX_TERRAIN_TYPES = [
	'openground', 'forest', 'fields_in_season', 'pond', 'roughground', 'village'
]

# descriptive text for terrain types
HEX_TERRAIN_DESC = {
	'openground' : 'Open Ground', 'forest' : 'Forest', 'fields_in_season' : 'Fields',
	'pond' : 'Pond', 'roughground' : 'Rough Ground', 'village' : 'Village'
}

# maximum length for randomly generate crew names
CREW_NAME_MAX_LENGTH = 20

# list of phases in a unit activation
PHASE_LIST = ['Crew Actions', 'Spotting', 'Movement', 'Combat']

# FUTURE full list:
#PHASE_LIST = ['Recovery', 'Command', 'Crew Actions', 'Spotting', 'Movement', 'Combat']

# crew action definitions
with open(DATAPATH + 'crew_action_defs.json') as data_file:
	CREW_ACTIONS = json.load(data_file)


##### Game Engine Constants #####
# Can be modified for a different game experience

# critical hit and miss thresholds
CRITICAL_HIT = 3.0
CRITICAL_MISS = 97.0

# base success chances for point fire attacks
# first column is for vehicle targets, second is everything else
PF_BASE_CHANCE = [
	[98.0, 88.0],			# same hex
	[92.0, 72.0],			# 1 hex range
	[89.5, 68.0],			# 2 hex range
	[83.0, 58.0],			# 3 "
	[72.0, 42.0],			# 4 "
	[58.0, 28.0],			# 5 "
	[42.0, 17.0]			# 6 "
]

# base success chances for armour penetration
AP_BASE_CHANCE = {
	'AT Rifle' : 28.0,
	'37L' : 83.0,
	'47S' : 72.0
}

# visible distances for crewmen when buttoned up and exposed
MAX_BU_LOS_DISTANCE = 3
MAX_LOS_DISTANCE = 6

ELEVATION_M = 10.0			# each elevation level represents x meters of height

# percentile LoS modifiers for terrain types
TERRAIN_LOS_MODS = {
	'openground' : 0.0,
	'roughground' : 5.0,
	'forest' : 40.0,
	'village' : 30.0,
	'fields_in_season' : 20.0,
	'pond' : 10.0
}

# effective height in meters of terrain LoS modifiers
TERRAIN_LOS_HEIGHT = {
	'openground' : 0.0,
	'roughground' : 0.0,
	'forest' : 20.0,
	'village' : 12.0,
	'fields_in_season' : 5.0,
	'pond' : 3.0
}

# base chance of getting a bonus move after moving into terrain
TERRAIN_BONUS_CHANCE = {
	'openground' : 80.0,
	'roughground' : 20.0,
	'forest' : 20.0,
	'village' : 10.0,
	'fields_in_season' : 50.0,
	'pond' : 0.0
}
# bonus move chance when moving along a dirt road
DIRT_ROAD_BONUS_CHANCE = 90.0

# maximum total modifer before a LoS is blocked by terrain
MAX_LOS_MOD = 60.0


##########################################################################################
#                                         Classes                                        #
##########################################################################################

# AI: controller for enemy and player-allied units
class AI:
	def __init__(self, owner):
		self.owner = owner
		self.disposition = None
	
	# print an AI report re: crew actions for this unit to the console, used for debugging
	def DoCrewActionReport(self):
		text = 'AI SPY: ' + self.owner.unit_id + ' set to disposition: '
		if self.disposition is None:
			text += 'Wait'
		else:
			text += self.disposition
		if self.owner.dummy:
			text += ' (dummy)'
		print text
		
		for position in self.owner.crew_positions:
			if position.crewman is None: continue
			text = ('AI SPY:  ' + position.crewman.GetFullName() +
					', in ' + position.name + ' position, current action: ' + 
					position.crewman.current_action)
			print text
	
	# do actions for this unit for this phase
	def DoPhaseAction(self):
		
		if not self.owner.alive: return
		
		# Crew Actions
		if scenario.game_turn['current_phase'] == 'Crew Actions':
			
			# set unit disposition for this turn
			roll = GetPercentileRoll()
			
			if roll >= 70.0:
				self.disposition = None
			elif roll <= 35.0:
				if self.owner.dummy:
					self.disposition = None
				else:
					self.disposition = 'Combat'
			else:
				self.disposition = 'Movement'
			
			# set crew actions according to disposition
			if self.disposition is None:
				for position in self.owner.crew_positions:
					if position.crewman is None: continue
					position.crewman.current_action = 'Spot'
			
			elif self.disposition == 'Movement':
				for position in self.owner.crew_positions:
					if position.crewman is None: continue
					if position.name == 'Driver':
						position.crewman.current_action = 'Drive'
					else:
						position.crewman.current_action = 'Spot'
			
			elif self.disposition == 'Combat':
				for position in self.owner.crew_positions:
					if position.crewman is None: continue
					if position.name in ['Commander/Gunner', 'Gunner/Loader', 'Gunner']:
						position.crewman.current_action = 'Operate Gun'
					elif position.name == 'Loader':
						position.crewman.current_action = 'Load Gun'
					else:
						position.crewman.current_action = 'Spot'
			
			if AI_SPY:
				self.DoCrewActionReport()
			return
		
		# Movement
		if scenario.game_turn['current_phase'] == 'Movement':
			if self.disposition != 'Movement':
				return
			
			move_done = False
			while not move_done:
				
				animate = False
				dist = GetHexDistance(self.owner.hx, self.owner.hy, scenario.player_unit.hx,
					scenario.player_unit.hy)
				if dist <= 7:
					animate = True
				
				# pick a random direction for move
				dir_list = [0,1,2,3,4,5]
				shuffle(dir_list)
				for direction in dir_list:
					(hx, hy) = GetAdjacentHex(self.owner.hx, self.owner.hy, direction)
					if (hx, hy) not in scenario.map_hexes: continue
					if scenario.map_hexes[(hx, hy)].terrain_type == 'pond':
						continue
					break
				
				if AI_SPY:
					text = ('AI SPY: ' + self.owner.unit_id + ' is moving to ' +
						str(hx) + ',' + str(hy))
					print text
				
				# pivot to face new direction if not already
				if self.owner.facing != direction:
					
					change = direction - self.owner.facing
					self.owner.facing = direction
					
					# rotate turret if any
					if self.owner.turret_facing is not None:
						self.owner.turret_facing = ConstrainDir(self.owner.turret_facing + change)
					
					if animate:
						UpdateUnitCon()
						UpdateScenarioDisplay()
						libtcod.console_flush()
						Wait(10)
				
				# do the move
				result = self.owner.MoveForward()
				if animate:
					UpdateUnitCon()
					UpdateUnitInfoCon()
					UpdateScenarioDisplay()
					libtcod.console_flush()
					Wait(10)
				
				# if move was not possible, end phase action
				if result == False:
					move_done = True
				# if no more moves, end phase action
				if self.owner.move_finished:
					move_done = True
			
			return
					
		# Combat
		if scenario.game_turn['current_phase'] == 'Combat':
			if self.disposition != 'Combat':
				return
			
			animate = False
			dist = GetHexDistance(self.owner.hx, self.owner.hy, scenario.player_unit.hx,
				scenario.player_unit.hy)
			if dist <= 7:
				animate = True
			
			# see if there are any potential targets
			target_list = []
			for unit in scenario.units:
				if not unit.alive: continue
				if unit.owning_player == self.owner.owning_player: continue
				if GetHexDistance(self.owner.hx, self.owner.hy, unit.hx,
					unit.hy) > 6: continue
				if (unit.hx, unit.hy) not in self.owner.fov: continue
				if not unit.known: continue
				target_list.append(unit)
			
			if len(target_list) == 0:
				if AI_SPY:
					print 'AI SPY: ' + self.owner.unit_id + ': no possible targets'
				return
			
			# select a random target from list
			unit = choice(target_list)
			
			# rotate turret if any to face target
			if self.owner.turret_facing is not None:
				direction = GetDirectionToward(self.owner.hx, self.owner.hy, unit.hx,
					unit.hy)
				if self.owner.turret_facing != direction:
					self.owner.turret_facing = direction
					
					if animate:
						UpdateUnitCon()
						UpdateScenarioDisplay()
						libtcod.console_flush()
						Wait(10)
			
			weapon = self.owner.weapon_list[0]
			
			# try the attack
			result = self.owner.Attack(weapon, unit, 'point_fire')
			if not result:
				if AI_SPY:
					print 'AI SPY: ' + self.owner.unit_id + ': could not attack'
					print 'AI SPY: ' + scenario.CheckAttack(self.owner, weapon, unit)
		

# Map Hex: a single hex-shaped block of terrain in a scenario
# roughly scaled to 160 m. in width
class MapHex:
	def __init__(self, hx, hy):
		self.hx = hx			# hex coordinates in the map
		self.hy = hy			# 0,0 is centre of map
		self.terrain_type = 'openground'
		self.elevation = 1		# elevation in steps above baseline
		self.dirt_roads = []		# list of directions linked by a dirt road
		
		self.unit_stack = []		# stack of units present in this hex
		self.objective = None		# status as an objective; if -1, not controlled
						#   by either player, otherwise 0 or 1
		
		# Pathfinding stuff
		self.parent = None
		self.g = 0
		self.h = 0
		self.f = 0
	
	# set elevation of hex
	# FUTURE: handle cliff edges here?
	def SetElevation(self, elevation):
		self.elevation = elevation
	
	# set terrain type
	def SetTerrainType(self, terrain_type):
		self.terrain_type = terrain_type
	
	# reset pathfinding info for this map hex
	def ClearPathInfo(self):
		self.parent = None
		self.g = 0
		self.h = 0
		self.f = 0
	
	# return total LoS modifier for this terrain hex
	# FUTURE: can also calculate effect of smoke, rain, etc.
	def GetTerrainMod(self):
		return TERRAIN_LOS_MODS[self.terrain_type]
	
	# check to see if this objective hex has been captured
	def CheckCapture(self):
		if self.objective is None: return False
		if len(self.unit_stack) == 0: return False
		
		for unit in self.unit_stack:
			if unit.dummy: continue
			if unit.owning_player != self.objective:
				self.objective = unit.owning_player
				return True
				
		


# Scenario: represents a single battle encounter
class Scenario:
	def __init__(self):
		
		# game turn, active player, and phase tracker
		self.game_turn = {
			'turn_number' : 1,		# current turn number in the scenario
			'hour' : 0,			# current time of day: hour in 24-hour clock
			'minute' : 0,			# " minute "
			'active_player' : 0,		# currently active player number
			'goes_first' : 0,		# which player side acts first in each turn
			'current_phase' : None		# current phase - one of PHASE_LIST
		}
		
		self.units = []				# list of units in the scenario
		self.player_unit = None			# pointer to the player unit
		
		self.finished = False			# have win/loss conditions been met
		self.winner = -1			# player number of scenario winner, -1 if None
		self.win_desc = ''			# description of win/loss conditions met
		
		self.selected_position = 0		# index of selected crewman in player unit
		self.selected_weapon = None		# currently selected weapon on player unit
		
		self.player_target_list = []		# list of possible enemy targets for player unit
		self.player_target = None		# current target of player unit
		self.player_attack_desc = ''		# text description of attack on player target
		self.player_los_active = False		# display of player's LoS to target is active
		
		###### Hex Map and Map Viewport #####
		
		# generate the hex map in the shape of a pointy-top hex
		# standard radius is 12 hexes not including centre hex
		self.map_hexes = {}
		map_radius = 12
		
		# create centre hex
		self.map_hexes[(0,0)] = MapHex(0,0)
		
		# add rings around centre
		for r in range(1, map_radius+1):
			hex_list = GetHexRing(0, 0, r)
			for (hx, hy) in hex_list:
				self.map_hexes[(hx,hy)] = MapHex(hx,hy)
		#print 'Generated ' + str(len(self.map_hexes.keys())) + ' map hexes'
		
		self.map_objectives = []		# list of map hex objectives
		self.highlighted_hex = None		# currently highlighted map hex
		
		##### Map VP
		self.map_vp = {}			# dictionary of map viewport hexes and
							#   their corresponding map hexes
		self.vp_hx = 0				# location and facing of center of
		self.vp_hy = 0				#   viewport on map
		self.vp_facing = 0
		
		# dictionary of screen display locations on the VP and their corresponding map hex
		self.hex_map_index = {}
		
		# dictionary of hex console images; newly generated each time scenario
		# starts or is resumed
		self.hex_consoles = {}
		
		# FUTURE: move this to a session object
		self.GenerateHexConsoles()
		
		
		
		
	# generate hex console images for scenario map
	def GenerateHexConsoles(self):
		self.hex_consoles = {}
		
		for terrain_type in HEX_TERRAIN_TYPES:
			
			# generate consoles for 4 different terrain heights
			consoles = []
			for elevation in range(4):
				consoles.append(libtcod.console_new(7, 5))
				libtcod.console_blit(LoadXP('hex_' + terrain_type + '.xp'),
					0, 0, 7, 5, consoles[elevation], 0, 0)
				libtcod.console_set_key_color(consoles[elevation], KEY_COLOR)
			
			# apply colour modifier to elevations 0, 2, 3
			for elevation in [0, 2, 3]:
				for y in range(5):
					for x in range(7):
						bg = libtcod.console_get_char_background(consoles[elevation],x,y)
						if bg == KEY_COLOR: continue
						bg = bg * (1.0 + float(elevation-1) * ELEVATION_SHADE)
						libtcod.console_set_char_background(consoles[elevation],x,y,bg)
			
			self.hex_consoles[terrain_type] = consoles
	
	# clear stored hex consoles
	def ClearHexConsoles(self):
		self.hex_consoles = {}
	
	# set up map viewport hexes based on viewport center position and facing
	def SetVPHexes(self):
		for (hx, hy) in VP_HEXES:
			map_hx = hx + self.vp_hx
			map_hy = hy + self.vp_hy
			# rotate based on viewport facing
			(hx, hy) = RotateHex(hx, hy, ConstrainDir(0 - self.vp_facing))
			self.map_vp[(hx, hy)] = (map_hx, map_hy)
	
	# center the map viewport on the player unit and rotate so that player unit is facing up
	def CenterVPOnPlayer(self):
		self.vp_hx = self.player_unit.hx
		self.vp_hy = self.player_unit.hy
		self.vp_facing = self.player_unit.facing
	
	# fill the hex map with terrain
	# does not (yet) clear any pre-existing terrain from the map!
	def GenerateTerrain(self):
		
		# return a path from hx1,hy1 to hx2,hy2 suitable for a dirt road
		def GenerateRoad(hx1, hy1, hx2, hy2):
			
			path = GetHexPath(hx1, hy1, hx2, hy2, road_path=True)
			
			# no path was possible
			if len(path) == 0:
				return False
			
			# create the road
			for n in range(len(path)):
				(hx1, hy1) = path[n]
				if n+1 < len(path):
					hx2, hy2 = path[n+1]
					direction = GetDirectionToAdjacent(hx1, hy1, hx2, hy2)
					self.map_hexes[(hx1, hy1)].dirt_roads.append(direction)
					
					direction = GetDirectionToAdjacent(hx2, hy2, hx1, hy1)
					self.map_hexes[(hx2, hy2)].dirt_roads.append(direction)
			
			return True
		
		# create a local list of all hx, hy locations in map
		map_hex_list = []
		for key, map_hex in self.map_hexes.iteritems():
			map_hex_list.append(key)
		
		# record total number of hexes in the map
		hex_num = len(map_hex_list)
		
		# terrain settings
		# FUTURE: will be supplied by battleground settings
		rough_ground_num = int(hex_num / 50)	# rough ground hexes
		
		hill_num = int(hex_num / 70)		# number of hills to generate
		hill_min_size = 4			# minimum width/height of hill area
		hill_max_size = 7			# maximum "
		
		forest_num = int(hex_num / 50)		# number of forest areas to generate
		forest_size = 6				# total maximum height + width of areas
		
		village_max = int(hex_num / 100)	# maximum number of villages to generate
		village_min = int(hex_num / 50)		# minimum "
		
		fields_num = int(hex_num / 50)		# number of tall field areas to generate
		field_min_size = 1			# minimum width/height of field area
		field_max_size = 3			# maximum "
		
		ponds_min = int(hex_num / 400)		# minimum number of ponds to generate
		ponds_max = int(hex_num / 80)		# maximum "
		
		
		##### Rough Ground #####
		for terrain_pass in range(rough_ground_num):
			(hx, hy) = choice(map_hex_list)
			self.map_hexes[(hx, hy)].SetTerrainType('roughground')
		
		##### Elevation / Hills #####
		for terrain_pass in range(hill_num):
			hex_list = []
			
			# determine upper left corner, width, and height of hill area
			(hx_start, hy_start) = choice(map_hex_list)
			hill_width = libtcod.random_get_int(0, hill_min_size, hill_max_size)
			hill_height = libtcod.random_get_int(0, hill_min_size, hill_max_size)
			hx_start -= int(hill_width / 2)
			hy_start -= int(hill_height / 2)
			
			# get a rectangle of hex locations
			hex_rect = GetHexRect(hx_start, hy_start, hill_width, hill_height)
			
			# determine how many points to use for hill generation
			min_points = int(len(hex_rect) / 10)
			max_points = int(len(hex_rect) / 3)
			hill_points = libtcod.random_get_int(0, min_points, max_points)
			
			# build a list of hill locations around random points
			for i in range(hill_points):
				(hx, hy) = choice(hex_rect)
				hex_list.append((hx, hy))
				for direction in range(6):
					hex_list.append(GetAdjacentHex(hx, hy, direction))
			
			# apply the hill locations if they are on map
			for (hx, hy) in hex_list:
				if (hx, hy) in self.map_hexes:
					self.map_hexes[(hx, hy)].SetElevation(2)
		
		##### Forests #####
		if forest_size < 2: forest_size = 2
		
		for terrain_pass in range(forest_num):
			hex_list = []
			(hx_start, hy_start) = choice(map_hex_list)
			width = libtcod.random_get_int(0, 1, forest_size-1)
			height = forest_size - width
			hx_start -= int(width / 2)
			hy_start -= int(height / 2)
			
			# get a rectangle of hex locations
			hex_rect = GetHexRect(hx_start, hy_start, width, height)
			
			# apply forest locations if they are on map
			for (hx, hy) in hex_rect:
				if (hx, hy) in self.map_hexes:
					# small chance of gaps in area
					if libtcod.random_get_int(0, 1, 15) == 1:
						continue
					self.map_hexes[(hx, hy)].SetTerrainType('forest')

		##### Villages #####
		num_villages = libtcod.random_get_int(0, village_min, village_max)
		for terrain_pass in range(num_villages):
			# determine size of village in hexes: 1,1,1,2,3 hexes total
			village_size = libtcod.random_get_int(0, 1, 5) - 2
			if village_size < 1: village_size = 1
			
			# find centre of village
			shuffle(map_hex_list)
			for (hx, hy) in map_hex_list:
				
				if self.map_hexes[(hx, hy)].terrain_type == 'forest':
					continue
				
				# create centre of village
				self.map_hexes[(hx, hy)].SetTerrainType('village')
				
				# handle large villages; if extra hexes fall off map they won't
				#  be added
				# TODO: possible to lose one or more additional hexes if they
				#   are already village hexes
				if village_size > 1:
					for extra_hex in range(village_size-1):
						(hx2, hy2) = GetAdjacentHex(hx, hy, libtcod.random_get_int(0, 0, 5))
						if (hx2, hy2) in map_hex_list:
							self.map_hexes[(hx2, hy2)].SetTerrainType('village')
				break
		
		##### In-Season Fields #####
		for terrain_pass in range(fields_num):
			hex_list = []
			(hx_start, hy_start) = choice(map_hex_list)
			width = libtcod.random_get_int(0, field_min_size, field_max_size)
			height = libtcod.random_get_int(0, field_min_size, field_max_size)
			hx_start -= int(width / 2)
			hy_start -= int(height / 2)
			
			# get a rectangle of hex locations
			hex_rect = GetHexRect(hx_start, hy_start, width, height)
			
			# apply forest locations if they are on map
			for (hx, hy) in hex_rect:
				if (hx, hy) not in map_hex_list:
					continue
					
				# don't overwrite villages
				if self.map_hexes[(hx, hy)].terrain_type == 'village':
					continue
				
				# small chance of overwriting forest
				if self.map_hexes[(hx, hy)].terrain_type == 'forest':
					if libtcod.random_get_int(0, 1, 10) <= 9:
						continue
				
				self.map_hexes[(hx, hy)].SetTerrainType('fields_in_season')

		##### Ponds #####
		num_ponds = libtcod.random_get_int(0, ponds_min, ponds_max)
		shuffle(map_hex_list)
		for terrain_pass in range(num_ponds):
			for (hx, hy) in map_hex_list:
				if self.map_hexes[(hx, hy)].terrain_type != 'openground':
					continue
				if self.map_hexes[(hx, hy)].elevation != 1:
					continue
				self.map_hexes[(hx, hy)].SetTerrainType('pond')
				break
		
		##### Dirt Road #####
		hx1, hy1 = 0, 12
		hx2, hy2 = 0, -12
		GenerateRoad(hx1, hy1, hx2, hy2)
			
	# set a given map hex as an objective, and set initial control state
	def SetObjectiveHex(self, hx, hy, owning_player):
		map_hex = self.map_hexes[(hx, hy)]
		map_hex.objective = owning_player
		self.map_objectives.append(map_hex)
	
	# proceed to next phase or player turn
	# if returns True, then play proceeds to next phase/turn automatically
	def NextPhase(self):
		
		# FUTURE: activate allied AI units here
		if self.game_turn['active_player'] == 0:
			pass
		
		# do end of phase stuff
		self.DoEndOfPhase()
		
		i = PHASE_LIST.index(self.game_turn['current_phase'])
		
		# end of player turn
		if i == len(PHASE_LIST) - 1:
			
			# end of first half of game turn, other player's turn
			if self.game_turn['active_player'] == self.game_turn['goes_first']:
				new_player = self.game_turn['active_player'] + 1
				if new_player == 2: new_player = 0
				self.game_turn['active_player'] = new_player
			
			# end of turn
			else:
				self.DoEndOfTurn()
				# scenario is over
				if self.finished:
					return False
			
			# return to first phase in list
			i = 0
		else:
			# next phase in list
			i += 1
		
		self.game_turn['current_phase'] = PHASE_LIST[i]
		
		# do start of phase stuff
		self.DoStartOfPhase()
		
		# if AI p[layer active, return now
		if self.game_turn['active_player'] == 1:
			return False
		
		# check for automatic next phase
		if self.game_turn['current_phase'] == 'Movement':
			# check for a crewman on a move action
			move_action = False
			if self.player_unit.CheckCrewAction(['Driver'], ['Drive', 'Drive Cautiously']):
				move_action = True
			
			if not move_action: return True
			
		elif self.game_turn['current_phase'] == 'Combat':
			# check for a crewman on a combat action
			combat_action = False
			if self.player_unit.CheckCrewAction(['Commander/Gunner'],['Operate Gun']):
				combat_action = True
			
			if not combat_action: return True
		
		# save game if passing back to player control
		SaveGame()
		
		return False
	
	# take care of automatic processes for the start of the current phase
	def DoStartOfPhase(self):
		
		if self.game_turn['current_phase'] == 'Crew Actions':
			
			# go through active units and generate list of possible crew actions
			for unit in self.units:
				if unit.owning_player != self.game_turn['active_player']:
					continue
				if not unit.alive: continue
			
				for position in unit.crew_positions:
					
					# no crewman in this position
					if position.crewman is None: continue
					
					action_list = []
					
					for action_name in CREW_ACTIONS:
						# action restricted to a list of positions
						if 'position_list' in CREW_ACTIONS[action_name]:
							if position.name not in CREW_ACTIONS[action_name]['position_list']:
								continue
						action_list.append(action_name)
					
					# copy over the list to the crewman
					position.crewman.action_list = action_list[:]
					
					# if previous action is no longer possible, cancel it
					if position.crewman.current_action is not None:
						if position.crewman.current_action not in action_list:
							position.crewman.current_action = None
		
		elif self.game_turn['current_phase'] == 'Spotting':
			
			# go through each active unit and recalculate FoV and do spot checks
			# for unknown or unidentified enemy units
			for unit in self.units:
				if unit.owning_player != self.game_turn['active_player']:
					continue
				if not unit.alive: continue
				
				# recalculate FoV
				unit.CalcFoV()
				if unit == scenario.player_unit:
					UpdateVPCon()
					UpdateUnitCon()
					UpdateScenarioDisplay()
					libtcod.console_flush()
				
				# dummy units can't spot
				if unit.dummy: continue
				
				# create a local list of crew positions in a random order
				position_list = sample(unit.crew_positions, len(unit.crew_positions))
				
				for position in position_list:
					if position.crewman is None: continue
					
					# FUTURE: check that crewman is able to spot
					
					spot_list = []
					for unit2 in self.units:
						if unit2.owning_player == unit.owning_player:
							continue
						if not unit2.alive:
							continue
						if unit2.known:
							continue
						if GetHexDistance(unit.hx, unit.hy, unit2.hx, unit2.hy) > MAX_LOS_DISTANCE:
							continue
						
						if (unit2.hx, unit2.hy) in position.crewman.fov:
							spot_list.append(unit2)
					
					if len(spot_list) > 0:
						unit.DoSpotCheck(choice(spot_list), position)
		
		elif self.game_turn['current_phase'] == 'Movement':
			
			for unit in self.units:
				if unit.owning_player != self.game_turn['active_player']:
					continue
				if not unit.alive: continue
				
				# reset flags
				unit.moved = False
				unit.move_finished = False
				unit.additional_moves_taken = 0
				unit.previous_facing = unit.facing
				unit.previous_turret_facing = unit.turret_facing
		
		elif self.game_turn['current_phase'] == 'Combat':
			
			# if player is active, handle their selected weapon and target list
			if self.game_turn['active_player'] == 0:
			
				# if no player weapon selected, try to select the first one in the list
				if self.selected_weapon is None:
					if len(self.player_unit.weapon_list) > 0:
						self.selected_weapon = self.player_unit.weapon_list[0]
					
				# rebuild list of potential targets
				self.RebuildPlayerTargetList()
				
				# clear player target if no longer possible
				if self.player_target is not None:
					if self.player_target not in self.player_target_list:
						self.player_target = None
				
				# turn on player LoS display
				self.player_los_active = True
				UpdateUnitCon()
				UpdateScenarioDisplay()
			
			# reset weapons for active player's units
			for unit in self.units:
				if unit.owning_player != self.game_turn['active_player']:
					continue
				if not unit.alive: continue
				
				unit.fired = False
				for weapon in unit.weapon_list:
					weapon.ResetForNewTurn()
	
	# do automatic events at the end of a phase
	def DoEndOfPhase(self):
		
		if self.game_turn['current_phase'] == 'Movement':
			
			# set movement flag for units that pivoted
			for unit in self.units:
				if unit.owning_player != self.game_turn['active_player']:
					continue
				if not unit.alive:
					continue
				
				if unit.facing is not None:
					if unit.facing != unit.previous_facing:
						unit.moved = True
		
		elif self.game_turn['current_phase'] == 'Combat':
			
			# clear any player LoS
			if self.game_turn['active_player'] == 0:
				self.player_los_active = False
				UpdateUnitCon()
				UpdateScenarioDisplay()
			
			# resolve unresolved hits on enemy units
			for unit in self.units:
				if unit.owning_player == self.game_turn['active_player']:
					continue
				if not unit.alive:
					continue
				unit.ResolveHits()

	# do automatic events at the end of a game turn
	def DoEndOfTurn(self):
		
		# check for win/loss conditions
		if not self.player_unit.alive:
			self.winner = 1
			self.finished = True
			self.win_desc = 'Your tank was destroyed.'
			return
		
		all_enemies_dead = True
		for unit in self.units:
			if unit.owning_player == 1 and unit.alive:
				all_enemies_dead = False
				break
		if all_enemies_dead:
			self.winner = 0
			self.finished = True
			self.win_desc = 'All enemy units in the area were destroyed.'
			return
		
		all_objectives_captured = True
		for map_hex in self.map_objectives:
			if map_hex.objective == 1:
				all_objectives_captured = False
				break
		if all_objectives_captured:
			self.winner = 0
			self.finished = True
			self.win_desc = 'All objectives in the area were captured.'
			return
		
		self.game_turn['turn_number'] += 1
		self.game_turn['active_player'] = self.game_turn['goes_first']
		
		# advance clock
		self.game_turn['minute'] += 1
		if self.game_turn['minute'] == 60:
			self.game_turn['minute'] = 0
			self.game_turn['hour'] += 1
		
		# check for objective capture
		for map_hex in self.map_objectives:
			if map_hex.CheckCapture():
				text = 'An objective was captured by '
				if map_hex.objective == 0:
					text += 'your forces'
				else:
					text += 'enemy forces'
				self.ShowMessage(text, hx=map_hex.hx, hy=map_hex.hy)
				
	
	# select the next or previous weapon on the player unit, looping around the list
	def SelectNextWeapon(self, forward):
		
		# no weapons to select
		if len(self.player_unit.weapon_list) == 0: return False
		
		# no weapon selected yet
		if self.selected_weapon is None:
			self.selected_weapon = self.player_unit.weapon_list[0]
			return True
		
		i = self.player_unit.weapon_list.index(self.selected_weapon)
		
		if forward:
			i+=1
		else:
			i-=1
		
		if i < 0:
			self.selected_weapon = self.player_unit.weapon_list[-1]
		elif i > len(self.player_unit.weapon_list) - 1:
			self.selected_weapon = self.player_unit.weapon_list[0]
		else:
			self.selected_weapon = self.player_unit.weapon_list[i]
		return True
	
	# rebuild the list of all enemy units that could be targeted by the player unit
	def RebuildPlayerTargetList(self):
		self.player_target_list = []
		
		for unit in self.units:
			if not unit.alive: continue
			if unit.owning_player == 0: continue
			if GetHexDistance(self.player_unit.hx, self.player_unit.hy, unit.hx,
				unit.hy) > 6: continue
			if (unit.hx, unit.hy) not in scenario.player_unit.fov: continue
			self.player_target_list.append(unit)
	
	# select the next enemy target for the player unit, looping around the list
	def SelectNextTarget(self, forward):
		
		# no targets possible
		if len(self.player_target_list) == 0: return False
		
		if self.player_target is None:
			self.player_target = self.player_target_list[0]
		else:
			i = self.player_target_list.index(self.player_target)
			
			if forward:
				i+=1
			else:
				i-=1
			
			if i < 0:
				self.player_target = self.player_target_list[-1]
			elif i > len(self.player_target_list) - 1:
				self.player_target = self.player_target_list[0]
			else:
				self.player_target = self.player_target_list[i]
	
		# see if target is valid
		self.player_attack_desc = self.CheckAttack(self.player_unit,
			self.selected_weapon, self.player_target)
			
		return True
	
	# calculate the odds of success of a ranged attack, return a dictionary of data
	# including base chance, modifiers, and final chance
	def CalcAttack(self, attacker, weapon, target, mode):
		
		profile = {}
		profile['type'] = mode
		modifier_list = []
		
		# calculate distance to target
		distance = GetHexDistance(attacker.hx, attacker.hy, target.hx, target.hy)
		
		# point fire attacks (eg. large guns)
		if mode == 'point_fire':
			
			# calculate base success chance
			if target.GetStat('category') == 'Vehicle':
				profile['base_chance'] = PF_BASE_CHANCE[distance][0]
			else:
				profile['base_chance'] = PF_BASE_CHANCE[distance][1]
		
			# calculate modifiers and build list of descriptions
			
			# description max length is 19 chars
			
			# attacker moved
			if attacker.moved:
				modifier_list.append(('Attacker Moved', -60.0))
			# TODO: elif weapon turret rotated
			
			# TODO: LoS modifier
			los = GetLoS(attacker.hx, attacker.hy, target.hx, target.hy)
			if los > 0.0:
				modifier_list.append(('Terrain', 0.0 - los))
			
			# target vehicle moved
			if target.moved and target.GetStat('category') == 'Vehicle':
				modifier_list.append(('Target Moved', -30.0))
			
			# target size
			size_class = target.GetStat('size_class')
			if size_class is not None:
				if size_class == 'Small':
					modifier_list.append(('Small Target', -7.0))
				elif size_class == 'Very Small':
					modifier_list.append(('Very Small Target', -18.0))
			
			# elevation
			elevation1 = self.map_hexes[(attacker.hx, attacker.hy)].elevation
			elevation2 = self.map_hexes[(target.hx, target.hy)].elevation
			if elevation2 > elevation1:
				modifier_list.append(('Higher Elevation', -20.0))
		
		# save the list of modifiers
		profile['modifier_list'] = modifier_list[:]
		
		# calculate total modifier
		total_modifier = 0.0
		for (desc, mod) in modifier_list:
			total_modifier += mod
		
		# calculate final chance of success
		profile['final_chance'] = RestrictChance(profile['base_chance'] + total_modifier)
		
		return profile
	
	# calculate an armour penetration attempt
	# also determines location hit on target
	def CalcAP(self, attacker, weapon, target, result):
		
		profile = {}
		profile['type'] = 'ap'
		modifier_list = []
		
		# determine location hit on target
		if libtcod.random_get_int(0, 1, 6) <= 4:
			location = 'Hull'
			turret_facing = False
		else:
			location = 'Turret'
			turret_facing = True
		
		facing = GetFacing(attacker, target, turret_facing=turret_facing)
		hit_location = (location + '_' + facing).lower()
		
		# generate a text description of location hit
		if target.turret_facing is None:
			location = 'Upper Hull'
		profile['location_desc'] = location + ' ' + facing
		
		# calculate base chance of penetration
		if weapon.GetStat('name') == 'AT Rifle':
			base_chance = AP_BASE_CHANCE['AT Rifle']
		else:
			gun_rating = weapon.GetStat('calibre')
			if weapon.GetStat('long_range') is not None:
				gun_rating += weapon.GetStat('long_range')
			if gun_rating not in AP_BASE_CHANCE:
				print 'ERROR: No AP base chance found for: ' + gun_rating
				return None
			base_chance = AP_BASE_CHANCE[gun_rating]
		
		profile['base_chance'] = base_chance
		
		# calculate modifiers
		
		# calibre/range modifier
		calibre = int(weapon.GetStat('calibre'))
		distance = GetHexDistance(attacker.hx, attacker.hy, target.hx, target.hy)
		if distance <= 1:
			if calibre <= 57:
				modifier_list.append(('Close Range', 7.0))
		elif distance == 5:
			modifier_list.append(('Medium Range', -7.0))
		elif distance == 6:
			if calibre < 65:
				modifier_list.append(('Long Range', -18.0))
			else:
				modifier_list.append(('Long Range', -7.0))
		
		# target armour modifier
		armour = target.GetStat('armour')
		if armour is not None:
			target_armour = int(armour[hit_location])
			if target_armour > 0:
				modifier = -7.0
				for i in range(target_armour - 1):
					modifier = modifier * 1.8
				
				modifier_list.append(('Target Armour', modifier))
				
				# apply critical hit modifier if any
				if result == 'CRITICAL HIT':
					modifier = abs(modifier) * 0.8
					modifier_list.append(('Critical Hit', modifier))
				
		
		# save the list of modifiers
		profile['modifier_list'] = modifier_list[:]
		
		# calculate total modifer
		total_modifier = 0.0
		for (desc, mod) in modifier_list:
			total_modifier += mod
		
		# calculate final chance of success
		profile['final_chance'] = RestrictChance(profile['base_chance'] + total_modifier)
		
		return profile
	
	# display an attack or AP profile to the screen and prompt to proceed
	def DisplayAttack(self, attacker, weapon, target, mode, profile):
		libtcod.console_clear(attack_con)
		
		# display the background outline
		libtcod.console_blit(LoadXP('attack_bkg.xp'), 0, 0, 0, 0, attack_con, 0, 0)
		
		# window title
		libtcod.console_set_default_background(attack_con, libtcod.darker_blue)
		libtcod.console_rect(attack_con, 1, 1, 24, 1, False, libtcod.BKGND_SET)
		libtcod.console_set_default_background(attack_con, libtcod.black)
		
		if profile['type'] == 'ap':
			text = 'Armour Penetration'
		else:
			text = 'Ranged Attack'
		libtcod.console_print_ex(attack_con, 13, 1, libtcod.BKGND_NONE,
			libtcod.CENTER, text)
		
		# attacker portrait if any
		libtcod.console_set_default_background(attack_con, PORTRAIT_BG_COL)
		libtcod.console_rect(attack_con, 1, 2, 24, 8, False, libtcod.BKGND_SET)
		
		# TEMP: in future will store portraits for every active unit type in session object
		if not (attacker.owning_player == 1 and not attacker.known):
			portrait = attacker.GetStat('portrait')
			if portrait is not None:
				libtcod.console_blit(LoadXP(portrait), 0, 0, 0, 0, attack_con, 1, 2)
		
		# attack description
		if profile['type'] == 'ap':
			text1 = target.GetName()
			text2 = 'hit by ' + weapon.GetStat('name')
			text3 = 'in ' + profile['location_desc']
		else:
			text1 = attacker.GetName()
			text2 = 'firing ' + weapon.GetStat('name') + ' at'
			text3 = target.unit_id
		
		libtcod.console_print_ex(attack_con, 13, 10, libtcod.BKGND_NONE,
			libtcod.CENTER, text1)
		libtcod.console_print_ex(attack_con, 13, 11, libtcod.BKGND_NONE,
			libtcod.CENTER, text2)
		libtcod.console_print_ex(attack_con, 13, 12, libtcod.BKGND_NONE,
			libtcod.CENTER, text3)
		
		# target portrait if any
		libtcod.console_set_default_background(attack_con, PORTRAIT_BG_COL)
		libtcod.console_rect(attack_con, 1, 13, 24, 8, False, libtcod.BKGND_SET)
		
		# TEMP: in future will store portraits for every active unit type in session object
		if not (target.owning_player == 1 and not target.known):
			portrait = target.GetStat('portrait')
			if portrait is not None:
				libtcod.console_blit(LoadXP(portrait), 0, 0, 0, 0, attack_con, 1, 13)
		
		# base chance
		text = 'Base Chance: ' + str(profile['base_chance']) + '%%'
		libtcod.console_print_ex(attack_con, 13, 23, libtcod.BKGND_NONE,
			libtcod.CENTER, text)
		
		# modifiers
		libtcod.console_set_default_background(attack_con, libtcod.darker_blue)
		libtcod.console_rect(attack_con, 1, 27, 24, 1, False, libtcod.BKGND_SET)
		libtcod.console_set_default_background(attack_con, libtcod.black)
		libtcod.console_print_ex(attack_con, 13, 27, libtcod.BKGND_NONE,
			libtcod.CENTER, 'Modifiers')
		
		y = 29
		if len(profile['modifier_list']) == 0:
			libtcod.console_print_ex(attack_con, 13, y, libtcod.BKGND_NONE,
				libtcod.CENTER, 'None')
		else:
			for (desc, mod) in profile['modifier_list']:
				libtcod.console_print(attack_con, 2, y, desc)
				
				# TODO: display more arrows if modifier is more severe
				if mod > 0.0:
					col = libtcod.green
					text = chr(232)
				else:
					col = libtcod.red
					text = chr(233)
				libtcod.console_set_default_foreground(attack_con, col)
				libtcod.console_print_ex(attack_con, 24, y, libtcod.BKGND_NONE,
					libtcod.RIGHT, text)
				libtcod.console_set_default_foreground(attack_con, libtcod.white)
				
				y += 1
		
		# final chance
		libtcod.console_set_default_background(attack_con, libtcod.darker_blue)
		libtcod.console_rect(attack_con, 1, 46, 24, 1, False, libtcod.BKGND_SET)
		libtcod.console_set_default_background(attack_con, libtcod.black)
		libtcod.console_print_ex(attack_con, 13, 46, libtcod.BKGND_NONE,
			libtcod.CENTER, 'Final Chance')
		
		# chance graph display
		x = int(ceil(24.0 * profile['final_chance'] / 100.0))
		libtcod.console_set_default_background(attack_con, libtcod.green)
		libtcod.console_rect(attack_con, 1, 49, x-1, 3, False, libtcod.BKGND_SET)
		
		libtcod.console_set_default_background(attack_con, libtcod.red)
		libtcod.console_rect(attack_con, x, 49, 25-x, 3, False, libtcod.BKGND_SET)
		
		# critical hit band
		libtcod.console_set_default_foreground(attack_con, libtcod.blue)
		for y in range(49, 52):
			libtcod.console_put_char(attack_con, 1, y, 221)
		
		# critical miss band
		libtcod.console_set_default_foreground(attack_con, libtcod.dark_grey)
		for y in range(49, 52):
			libtcod.console_put_char(attack_con, 24, y, 222)
		
		libtcod.console_set_default_foreground(attack_con, libtcod.white)
		libtcod.console_set_default_background(attack_con, libtcod.black)
		
		text = str(profile['final_chance']) + '%%'
		libtcod.console_print_ex(attack_con, 13, 50, libtcod.BKGND_NONE,
			libtcod.CENTER, text)
		
		# display prompts
		libtcod.console_set_default_foreground(attack_con, libtcod.light_blue)
		libtcod.console_print(attack_con, 6, 57, 'Enter')
		libtcod.console_set_default_foreground(attack_con, libtcod.white)
		libtcod.console_print(attack_con, 12, 57, 'Continue')
		
		# blit the finished console to the screen
		libtcod.console_blit(attack_con, 0, 0, 0, 0, con, 0, 0)
		libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
		libtcod.console_flush()
	
	# do a roll, animate the attack console, and display the results
	def DoAttackRoll(self, profile):
		
		# animate roll indicators randomly
		for i in range(3):
			x = libtcod.random_get_int(0, 1, 24)
			libtcod.console_put_char(attack_con, x, 48, 233)
			libtcod.console_put_char(attack_con, x, 52, 232)
			
			libtcod.console_blit(attack_con, 0, 0, 0, 0, con, 0, 0)
			libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
			libtcod.console_flush()
			
			Wait(20)
			
			libtcod.console_put_char(attack_con, x, 48, 0)
			libtcod.console_put_char(attack_con, x, 52, 0)
		
		roll = GetPercentileRoll()
		
		# display final roll indicators
		x = int(ceil(24.0 * roll / 100.0))
		
		# make sure only critical hits and misses appear in their columns
		if roll > CRITICAL_HIT and x == 1: x = 2
		if roll < CRITICAL_MISS and x == 24: x = 23
		
		libtcod.console_put_char(attack_con, x, 48, 233)
		libtcod.console_put_char(attack_con, x, 52, 232)
		
		if profile['type'] == 'ap':
			
			if roll >= CRITICAL_MISS:
				text = 'NO PENETRATION'
			elif roll <= CRITICAL_HIT:
				text = 'PENETRATED'
			elif roll <= profile['final_chance']:
				text = 'PENETRATED'
			else:
				text = 'NO PENETRATION'
		else:
			if roll >= CRITICAL_MISS:
				text = 'MISS'
			elif roll <= CRITICAL_HIT:
				text = 'CRITICAL HIT'
			elif roll <= profile['final_chance']:
				text = 'HIT'
			else:
				text = 'MISS'
		
		libtcod.console_print_ex(attack_con, 13, 54, libtcod.BKGND_NONE,
			libtcod.CENTER, text)
		
		# blit the finished console to the screen
		libtcod.console_blit(attack_con, 0, 0, 0, 0, con, 0, 0)
		libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
		libtcod.console_flush()
		
		return text
		
		if profile['type'] == 'ap':
			if roll <= profile['final_chance']:
				return 'penetrated'
			else:
				return 'no_penetrate'
		
		if roll <= CRITICAL_HIT:
			return 'critical_hit'
		if roll <= profile['final_chance']:
			return 'hit'
		return 'miss'
	
	# given a combination of an attacker, weapon, and target, see if this would be a
	# valid attack; if not, return a text description of why not
	def CheckAttack(self, attacker, weapon, target):
		
		# check range to target
		distance = GetHexDistance(attacker.hx, attacker.hy, target.hx, target.hy)
		if distance > weapon.max_range:
			return 'Beyond maximum weapon range'
		
		# check covered arc
		if weapon.GetStat('mount') == 'Turret':
			direction = attacker.turret_facing
		else:
			direction = attacker.facing
		if (target.hx - attacker.hx, target.hy - attacker.hy) not in HEXTANTS[direction]:
			return "Outside of weapon's covered arc"
		
		# check LoS
		if GetLoS(attacker.hx, attacker.hy, target.hx, target.hy) == -1.0:
			return 'No line of sight to target'
		
		# check that weapon can fire
		if weapon.fired:
			return 'Weapon already fired this turn'
		
		# TEMP: assume that attack is point fire
		if not target.known:
			return 'Target not spotted'

		# check crew order
		# TEMP: need to make more specific to this weapon
		if not attacker.CheckCrewAction(['Commander/Gunner', 'Gunner/Loader', 'Gunner'], ['Operate Gun']):
			return 'Crewman not on Operate Gun order'

		# attack can proceed
		return ''
	
	# calculate the chance of a unit getting a bonus move after a given move
	# hx, hy is the move destination hex
	def CalcBonusMove(self, unit, hx, hy):
		
		# check for dirt road link
		direction = GetDirectionToAdjacent(unit.hx, unit.hy, hx, hy)
		if direction in self.map_hexes[(unit.hx, unit.hy)].dirt_roads:
			chance = DIRT_ROAD_BONUS_CHANCE
		else:
			chance = TERRAIN_BONUS_CHANCE[self.map_hexes[(hx, hy)].terrain_type]
		
		# elevation change modifier
		if self.map_hexes[(hx, hy)].elevation > self.map_hexes[(unit.hx, unit.hy)].elevation:
			chance = chance * 0.5
		
		# movement class modifier
		movement_class = unit.GetStat('movement_class')
		if movement_class is not None:
			if movement_class == 'Fast Tank':
				chance += 15.0
		
		# direct driver modifier
		if unit.CheckCrewAction(['Commander', 'Commander/Gunner'], ['Direct Driver']):
			chance += 15.0
		
		# previous bonus move modifier
		if unit.additional_moves_taken > 0:
			for i in range(unit.additional_moves_taken):
				chance = chance * 0.6
		
		return RestrictChance(chance)
	
	# display a pop-up message overtop the map viewport
	def ShowMessage(self, message, hx=None, hy=None):
		
		# enable hex highlight if any
		if hx is not None and hy is not None:
			self.highlighted_hex = (hx, hy)
			UpdateUnitCon()
			UpdateScenarioDisplay()
		
		# FUTURE: determine if window needs to be shifted to bottom half of screen
		# so that highlighted hex is not obscured
		
		libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
		libtcod.console_blit(popup_bkg, 0, 0, 0, 0, 0, 44, 13)
		y = 14
		lines = wrap(message, 27)
		# max 7 lines tall
		for line in lines[:7]:
			libtcod.console_print(0, 45, y, line)
			y += 1
		
		libtcod.console_flush()
		
		# FUTURE: get message pause time from settings
		Wait(len(lines) * 30)
		
		# clear hex highlight if any
		if hx is not None and hy is not None:
			self.highlighted_hex = None
			UpdateUnitCon()
			UpdateScenarioDisplay()
		else:
			libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
		libtcod.console_flush()


# Crew Class: represents a crewman in a vehicle or a single member of a unit's personnel
class Crew:
	def __init__(self, nation):
		self.name = self.GenerateName(nation)		# first and last name
		self.nation = nation
		self.action_list = []				# list of possible special actions
		self.current_action = 'Spot'			# currently active action
		
		self.fov = set()				# set of visible hexes
	
	def GenerateName(self, nation):
		
		# get list of possible first and last names
		with open(DATAPATH + 'nation_defs.json') as data_file:
			nations = json.load(data_file)
		
		for tries in range(300):
			first_name = choice(nations[nation]['first_names'])
			surname = choice(nations[nation]['surnames'])
			
			return (first_name, surname)
	
	# return the crewman's full name as a string
	def GetFullName(self):
		(first_name, surname) = self.name
		full_name = first_name + ' '.encode('utf-8') + surname
		
		# TODO - need to normalize special characters in Polish names
		# FUTURE: will have their own glyphs as part of font
		CODE = {
			u'Ś' : 'S', u'Ż' : 'Z', u'Ł' : 'L',
			u'ą' : 'a', u'ć' : 'c', u'ę' : 'e', u'ł' : 'l', u'ń' : 'n', u'ó' : 'o',
			u'ś' : 's', u'ź' : 'z', u'ż' : 'z'
		}
		
		fixed_name = u''
		for i in range(len(full_name)):
			if full_name[i] in CODE:
				new_char = CODE[full_name[i]]
				fixed_name += new_char.encode('utf-8')
			else:
				fixed_name += full_name[i]
		
		return fixed_name.encode('IBM850')
	
	# set a new action; if True, select next in list, otherwise previous
	def SetAction(self, forward):
		
		# no further actions possible
		if len(self.action_list) == 1:
			return False
		
		i = self.action_list.index(self.current_action)
		
		if forward:
			if i == len(self.action_list) - 1:
				self.current_action = self.action_list[0]
			else:
				self.current_action = self.action_list[i+1]
		
		else:
			if i == 0:
				self.current_action = self.action_list[-1]
			else:
				self.current_action = self.action_list[i-1]
		
		return True


# Crew Position class: represents a crew position on a vehicle or gun
class CrewPosition:
	def __init__(self, name, location, hatch, hatch_group, open_visible, closed_visible):
		self.name = name
		self.location = location
		self.crewman = None			# pointer to crewman currently in this position
		
		# hatch existence and status
		self.hatch_open = True
		self.hatch = hatch
		self.hatch_group = None
		if hatch_group is not None:
			self.hatch_group = int(hatch_group)
		
		# visible hextants when hatch is open/closed
		self.open_visible = []
		if open_visible is not None:
			for direction in open_visible:
				self.open_visible.append(int(direction))
		self.closed_visible = []
		if closed_visible is not None:
			for direction in closed_visible:
				self.closed_visible.append(int(direction))
	
	# toggle hatch open/closed status
	def ToggleHatch(self):
		if not self.hatch: return False
		self.hatch_open = not self.hatch_open
		# FUTURE: also toggle hatches in same group
		return True


# Weapon Class: represents a weapon mounted on or carried by a unit
class Weapon:
	def __init__(self, stats):
		self.stats = stats
		
		# some weapons need a descriptive name generated
		if 'name' not in self.stats:
			if self.GetStat('type') == 'Gun':
				text = self.GetStat('calibre') + 'mm'
				if self.GetStat('long_range') is not None:
					text += '(' + self.GetStat('long_range') + ')'
				self.stats['name'] = text
			else:
				self.stats['name'] = self.GetStat('type')
		
		# save maximum range as an int
		self.max_range = 6
		if 'max_range' in self.stats:
			self.max_range = int(self.stats['max_range'])
			del self.stats['max_range']
		else:
			if self.stats['type'] == 'Coax MG':
				self.max_range = 4
			elif self.stats['type'] == 'Hull MG':
				self.max_range = 2
		
		self.InitScenarioStats()

	# set up any data that is unique to a scenario
	def InitScenarioStats(self):
		self.fired = False
	
	# reset gun for start of new turn
	def ResetForNewTurn(self):
		self.fired = False
	
	# check for the value of a stat, return None if stat not present
	def GetStat(self, stat_name):
		if stat_name not in self.stats:
			return None
		return self.stats[stat_name]
		


# Unit Class: represents a single vehicle or gun, or a squad or small team of infantry
class Unit:
	def __init__(self, unit_id):
		
		self.unit_id = unit_id			# unique ID for unit type
		self.ai = None				# AI controller
		self.dummy = False			# unit is a false report, erased upon reveal
		
		# load unit stats from JSON file
		with open(DATAPATH + 'unit_type_defs.json') as data_file:
			unit_types = json.load(data_file)
		if unit_id not in unit_types:
			print 'ERROR: Could not find unit id: ' + unit_id
			return
		self.stats = unit_types[unit_id].copy()
		
		self.owning_player = None		# player that controls this unit
		self.nation = None			# nation of unit's crew
		self.crew_list = []			# list of pointers to crew/personnel
		
		self.crew_positions = []		# list of crew positions
		
		if 'crew_positions' in self.stats:
			for position in self.stats['crew_positions']:
				name = position['name']
				location = position['location']
				
				hatch = False
				if 'hatch' in position:
					hatch = True
				
				hatch_group = None
				if 'hatch_group' in position:
					hatch_group = position['hatch_group']
				
				open_visible = None
				if 'open_visible' in position:
					open_visible = position['open_visible']
				
				closed_visible = None
				if 'closed_visible' in position:
					closed_visible = position['closed_visible']
				
				self.crew_positions.append(CrewPosition(name, location,
					hatch, hatch_group, open_visible, closed_visible))
		
		self.weapon_list = []			# list of weapon systems
		weapon_list = self.stats['weapon_list']
		if weapon_list is not None:
			for weapon in weapon_list:
				
				# TEMP - skip adding MGs
				if weapon['type'] in ['Coax MG', 'Hull MG']:
					continue
				
				# create a Weapon object and store in unit's weapon list
				new_weapon = Weapon(weapon)
				self.weapon_list.append(new_weapon)
			
			# clear this stat since we don't need it any more
			self.stats['weapon_list'] = None
		
		self.InitScenarioStats()

	# set up any data that is unique to a scenario
	def InitScenarioStats(self):
		self.alive = True			# unit is not out of action
		self.dummy = False			# unit will disappear when spotted - AI units only
		self.known = False			# unit is known to the opposing side
		self.identified = False			# FUTURE: unit type has been identifed
		
		self.fp_to_resolve = 0			# fp from attacks to be resolved at end of phase
		self.ap_hits_to_resolve = []		# list of unresolved AP hits
		
		self.hx = 0				# hex location in the scenario map
		self.hy = 0
		self.facing = None			# facing direction: guns and vehicles must have this set
		self.previous_facing = None		# hull facing before current action
		self.turret_facing = None		# facing of main turret on unit
		self.previous_turret_facing = None	# turret facing before current action
		self.misses_turns = 0			# turns outstanding left to be missed
		
		self.acquired_target = None		# tuple: unit has acquired this unit to this level (1/2)
		
		self.screen_x = 0			# draw location on the screen
		self.screen_y = 0			#   set by DrawMe()
		self.vp_hx = None			# location in viewport if any
		self.vp_hy = None			# "
		self.anim_x = 0				# animation location in console
		self.anim_y = 0
		
		# action flags
		self.used_up_moves = False		# if true, unit has no move actions remaining this turn
		self.moved = False			# unit moved or pivoted in its previous movement phase
		self.move_finished = False		# unit has no additional moves left this turn
		self.additional_moves_taken = 0		# how many bonus moves this unit has had this turn
		self.fired = False			# unit fired 1+ weapons this turn
		
		# status flags
		self.pinned = False
		self.broken = False
		self.immobilized = False
		self.deployed = False
		
		# field of view
		self.fov = set()			# set of visible hexes for this unit
	
	# return the value of a stat
	def GetStat(self, stat_name):
		if stat_name in self.stats:
			return self.stats[stat_name]
		return None
	
	# get a descriptive name of this unit
	def GetName(self):
		if self.owning_player == 1 and not self.known:
			return 'Unknown Unit'
		return self.unit_id
	
	# calculate which hexes are visible to this unit
	def CalcFoV(self):
		
		# clear set of visible hexes
		self.fov = set()
		
		# can always see own hex
		self.fov.add((self.hx, self.hy))
		
		# start field of view calculations
		#start_time = time.time()
		
		# go through crew and calculate FoV for each, adding each hex to
		# unit FoV set
		for position in self.crew_positions:
			if position.crewman is None: continue
			
			position.crewman.fov = set()
			position.crewman.fov.add((self.hx, self.hy))
			
			visible_hextants = []
			if not position.hatch:
				visible_hextants = position.closed_visible[:]
				max_distance = MAX_BU_LOS_DISTANCE
			else:
				if position.hatch_open:
					visible_hextants = position.open_visible[:]
					max_distance = MAX_LOS_DISTANCE
				else:
					visible_hextants = position.closed_visible[:]
					max_distance = MAX_BU_LOS_DISTANCE
			
			# restrict visible hextants and max distance if crewman did a
			# special action last turn
			if position.crewman.current_action is not None:
				action = CREW_ACTIONS[position.crewman.current_action]
				if 'fov_hextants' in action:
					visible_hextants = []
					for text in action['fov_hextants']:
						visible_hextants.append(int(text))
				if 'fov_range' in action:
					if int(action['fov_range']) < max_distance:
						max_distance = int(action['fov_range'])
			
			# rotate visible hextants based on current turret/hull facing
			if position.location == 'Turret':
				direction = self.turret_facing
			else:
				direction = self.facing
			if direction != 0:
				for i, hextant in enumerate(visible_hextants):
					visible_hextants[i] = ConstrainDir(hextant + direction)
			
			# go through hexes in each hextant and check LoS if within spotting distance
			for hextant in visible_hextants:
				for (hxm, hym) in HEXTANTS[hextant]:
					
					# check that it's within range
					if GetHexDistance(0, 0, hxm, hym) > max_distance:
						continue
					
					hx = self.hx + hxm
					hy = self.hy + hym
					
					# check that it's on the map
					if (hx, hy) not in scenario.map_hexes:
						continue
					
					# check for LoS to hex
					if GetLoS(self.hx, self.hy, hx, hy) != -1.0:
						position.crewman.fov.add((hx, hy))
			
			# add this crewman's visisble hexes to that of unit
			self.fov = self.fov | position.crewman.fov
		
		#end_time = time.time()
		#time_taken = round((end_time - start_time) * 1000, 3) 
		#print 'FoV calculation for ' + self.unit_id + ' took ' + str(time_taken) + ' ms.'
	
	# generate a new crew sufficent to man all crew positions
	def GenerateNewCrew(self):
		for position in self.crew_positions:
			self.crew_list.append(Crew(self.nation))
			position.crewman = self.crew_list[-1]
	
	# draw this unit to the given viewport hex on the unit console
	def DrawMe(self, vp_hx, vp_hy):
		
		# don't display if not alive any more
		if not self.alive: return
		
		# record location in viewport
		self.vp_hx = vp_hx
		self.vp_hy = vp_hy
		
		# use animation position if any, otherwise calculate draw position
		if self.anim_x !=0 and self.anim_y != 0:
			x, y = self.anim_x, self.anim_y
		else:
			(x,y) = PlotHex(vp_hx, vp_hy)
		
		# determine foreground color to use
		if self.owning_player == 1:
			if not self.known:
				col = UNKNOWN_UNIT_COL
			else:
				col = ENEMY_UNIT_COL
		else:	
			if not self.known:
				col = libtcod.grey
			else:
				col = libtcod.white
		
		libtcod.console_put_char_ex(unit_con, x, y, self.GetDisplayChar(),
			col, libtcod.black)
		
		# record draw position on unit console
		self.screen_x = x
		self.screen_y = y
		
		# determine if we need to display a turret / gun depiction
		if self.GetStat('category') == 'Infantry': return
		if self.owning_player == 1 and not self.known: return
		
		# use turret facing if present, otherwise hull facing
		if self.turret_facing is not None:
			facing = self.turret_facing
		else:
			facing = self.facing
		
		# determine location to draw character
		direction = ConstrainDir(facing - scenario.vp_facing)
		x_mod, y_mod = PLOT_DIR[direction]
		char = TURRET_CHAR[direction]
		libtcod.console_put_char_ex(unit_con, x+x_mod, y+y_mod, char, col, libtcod.black)
		
	# return the display character to use on the map viewport
	def GetDisplayChar(self):
		# player unit
		if scenario.player_unit == self: return '@'
		
		# unknown enemy unit
		if self.owning_player == 1 and not self.known: return '?'
		
		unit_category = self.GetStat('category')
		
		# infantry
		if unit_category == 'Infantry': return 176
		
		# gun, set according to deployed status / hull facing
		if unit_category == 'Gun':
			if self.facing is None:		# facing not yet set
				return '!'
			direction = ConstrainDir(self.facing - scenario.player_unit.facing)
			if not self.deployed:
				return 124
			elif direction in [5, 0, 1]:
				return 232
			elif direction in [2, 3, 4]:
				return 233
			else:
				return '!'		# should not happen
		
		# vehicle
		if unit_category == 'Vehicle':
			
			# turretless vehicle
			if self.turret_facing is None:
				return 249
			return 9

		# default
		return '!'
	
	# attempt to move forward into next map hex
	# returns True if move was a success, false if not
	def MoveForward(self):
		
		# no moves remaining
		if self.move_finished:
			return False
		
		# make sure crewman can drive
		if not self.CheckCrewAction(['Driver'], ['Drive', 'Drive Cautiously']):
			return False
		
		# determine target hex
		(hx, hy) = GetAdjacentHex(self.hx, self.hy, self.facing)
		
		# target hex is off map
		if (hx, hy) not in scenario.map_hexes:
			return False
		
		map_hex2 = scenario.map_hexes[(hx, hy)]
		
		# target hex can't be entered
		if map_hex2.terrain_type == 'pond':
			return False
		
		# already occupied by enemy
		for unit in map_hex2.unit_stack:
			if unit.owning_player != self.owning_player:
				return False
		
		# calculate bonus move chance
		chance = scenario.CalcBonusMove(self, hx, hy)
		
		# do movement animation if applicable
		distance1 = GetHexDistance(self.hx, self.hy, scenario.player_unit.hx,
			scenario.player_unit.hy)
		distance2 = GetHexDistance(hx, hy, scenario.player_unit.hx,
			scenario.player_unit.hy)
		if distance1 <= 6 and distance2 <= 6:
			x1, y1 = self.screen_x, self.screen_y
			direction = GetDirectionToAdjacent(self.hx, self.hy, hx, hy)
			direction = ConstrainDir(direction - scenario.player_unit.facing)
			(new_vp_hx, new_vp_hy) = GetAdjacentHex(self.vp_hx, self.vp_hy, direction)
			(x2,y2) = PlotHex(new_vp_hx, new_vp_hy)
			line = GetLine(x1,y1,x2,y2)
			for (x,y) in line[1:-1]:
				self.anim_x = x
				self.anim_y = y
				UpdateUnitCon()
				UpdateScenarioDisplay()
				libtcod.console_flush()
				Wait(8)
			self.anim_x = 0
			self.anim_y = 0
		
		# remove unit from old map hex unit stack
		map_hex1 = scenario.map_hexes[(self.hx, self.hy)]
		map_hex1.unit_stack.remove(self)
		
		self.hx = hx
		self.hy = hy
		
		# add to new map hex unit stack
		map_hex2.unit_stack.append(self)
		
		# recalculate new FoV for unit
		self.CalcFoV()
		
		# set flag
		self.moved = True
		
		# check for bonus move
		roll = GetPercentileRoll()
		if roll <= chance:
			self.additional_moves_taken += 1
		else:
			self.move_finished = True
		
		return True
	
	# pivot the unit facing one hextant
	def Pivot(self, clockwise):
		
		if self.facing is None: return False
		
		# no moves remaining
		if self.move_finished:
			return False
		
		# make sure crewman can drive
		if not self.CheckCrewAction(['Driver'], ['Drive', 'Drive Cautiously']):
			return False
		
		if clockwise:
			change = 1
		else:
			change = -1
	
		self.facing = ConstrainDir(self.facing + change)
		
		# move turret if any along with hull
		if self.turret_facing is not None:
			self.turret_facing = ConstrainDir(self.turret_facing + change)
		
		# recalculate FoV for unit
		self.CalcFoV()
		
		return True
	
	# rotate the turret facing one hextant
	# only used by player unit for now, AI units have their own procedure in the AI object
	def RotateTurret(self, clockwise):
		
		if self.turret_facing is None:
			return False
		
		# make sure crewman on correct action
		if not self.CheckCrewAction(['Gunner', 'Commander/Gunner'], ['Operate Gun']):
			return False
		
		if clockwise:
			change = 1
		else:
			change = -1
		
		self.turret_facing = ConstrainDir(self.turret_facing + change)
		
		# recalculate FoV for unit
		self.CalcFoV()
		
		return True
	
	# start an attack with the given weapon on the given target
	def Attack(self, weapon, target, mode):
		
		# check to see that correct data has been supplied
		if weapon is None or target is None:
			return False
		
		# make sure attack is possible
		result = scenario.CheckAttack(self, weapon, target)
		if result != '':
			return False
		
		# set flags
		weapon.fired = True
		self.fired = True
		
		# TEMP - not needed any more?
		#self.CalcFoV()
		
		# display message if player is the target
		if target == scenario.player_unit:
			text = self.GetName() + ' fires at you!'
			scenario.ShowMessage(text, hx=self.hx, hy=self.hy)
		
		# TODO: display attack animation
		
		# calculate the attack profile
		attack_profile = scenario.CalcAttack(self, weapon, target, mode)
		
		# display the attack to the screen
		scenario.DisplayAttack(self, weapon, target, mode, attack_profile)
		WaitForEnter()
		
		# do the roll and display results to the screen
		result = scenario.DoAttackRoll(attack_profile)
		WaitForEnter()
		
		# break here if attack had no effect
		if result in ['MISS', 'NO PENETRATION']: return True
		
		# record AP hit to be resolved if target was a vehicle
		if target.GetStat('category') == 'Vehicle':
			target.ap_hits_to_resolve.append((self, weapon, result))
		
		return True
	
	# resolve all unresolved hits on this unit, triggered at end of enemy combat phase
	def ResolveHits(self):
		
		# no hits to resolve
		if len(self.ap_hits_to_resolve) == 0:
			return
		
		for (attacker, weapon, result) in self.ap_hits_to_resolve:
			
			# calcualte AP profile
			profile = scenario.CalcAP(attacker, weapon, self, result)
			
			# display the profile to the screen
			scenario.DisplayAttack(attacker, weapon, self, result, profile)
			WaitForEnter()
			
			# do the roll and display results to the screen
			result = scenario.DoAttackRoll(profile)
			WaitForEnter()
			
			# apply result
			if result == 'PENETRATED':
				self.DestroyMe()
			
			# unit was destroyed
			if not self.alive: return
	
	# destroy this unit and remove it from the scenario map
	def DestroyMe(self):
		self.alive = False
		scenario.map_hexes[(self.hx, self.hy)].unit_stack.remove(self)	
		UpdateUnitCon()
		UpdateScenarioDisplay()
	
	# roll a spotting check from this unit to another using the given crew position
	def DoSpotCheck(self, target, position):
		
		chance = 100.0
		
		# distance modifier
		distance = GetHexDistance(self.hx, self.hy, target.hx, target.hy)
		
		for i in range(distance):
			chance = chance * 0.9
		
		# terrain
		los = GetLoS(self.hx, self.hy, target.hx, target.hy)
		if los > 0.0:
			chance -= los
		
		# target size
		size_class = target.GetStat('size_class')
		if size_class is not None:
			if size_class == 'Small':
				chance -= 7.0
			elif size_class == 'Very Small':
				chance -= 18.0
		
		# spotter movement
		if self.moved:
			chance = chance * 0.75
		# target movement
		elif target.moved:
			chance = chance * 1.5
		
		# target fired
		if target.fired:
			chance = chance * 2.0
		
		chance = RestrictChance(chance)
		
		# special: automatic spot cases
		if distance <= 2 and los == 0.0:
			chance = 100.0
		
		roll = GetPercentileRoll()
		
		if roll <= chance:
			target.SpotMe()
			# display pop-up message window
			
			if self == scenario.player_unit:
				
				if target.dummy:
					text = (position.crewman.GetFullName() + ' says: ' + 
						'Thought there was something there...')
				else:
					text = (position.crewman.GetFullName() + ' says: ' + 
						target.GetName() + ' ' + target.GetStat('class') +
						' spotted!')
				scenario.ShowMessage(text, hx=target.hx, hy=target.hy)
			else:
				text = 'You have been spotted!'
				scenario.ShowMessage(text, hx=self.hx, hy=self.hy)
			
	# reveal this unit after being spotted
	def SpotMe(self):
		
		# dummy units are removed instead
		if self.dummy:
			self.DestroyMe()
			return
		
		self.known = True
		UpdateUnitCon()
		UpdateUnitInfoCon()
		UpdateScenarioDisplay()
	
	# check for a crewman in the given position and check that their action is
	# set to one of a given list
	def CheckCrewAction(self, position_list, action_list):
		
		for position in self.crew_positions:
			if position.name in position_list:
				if position.crewman is None: continue
				
				if len(action_list) == 0: return True
				
				if position.crewman.current_action in action_list:
					return True
		return False



##########################################################################################
#                                  General Functions                                     #
##########################################################################################

# return a random float between 0.0 and 100.0
def GetPercentileRoll():
	return float(libtcod.random_get_int(0, 1, 1000)) / 10.0


# restrict odds to between 3.0 and 97.0
def RestrictChance(chance):
	if chance < 3.0: return 3.0
	if chance > 97.0: return 97.0
	return chance


# load a console image from an .xp file
def LoadXP(filename):
	xp_file = gzip.open(DATAPATH + filename)
	raw_data = xp_file.read()
	xp_file.close()
	xp_data = xp_loader.load_xp_string(raw_data)
	console = libtcod.console_new(xp_data['width'], xp_data['height'])
	xp_loader.load_layer_to_console(console, xp_data['layer_data'][0])
	return console


# returns a path from one hex to another, avoiding impassible and difficult terrain
# based on function from ArmCom 1, which was based on:
# http://stackoverflow.com/questions/4159331/python-speed-up-an-a-star-pathfinding-algorithm
# http://www.policyalmanac.org/games/aStarTutorial.htm
def GetHexPath(hx1, hy1, hx2, hy2, unit=None, road_path=False):
	
	# retrace a set of nodes and return the best path
	def RetracePath(end_node):
		path = []
		node = end_node
		done = False
		while not done:
			path.append((node.hx, node.hy))
			if node.parent is None: break	# we've reached the end
			node = node.parent	
		path.reverse()
		return path
	
	# clear any old pathfinding info
	for key, map_hex in scenario.map_hexes.iteritems():
		map_hex.ClearPathInfo()
	
	node1 = scenario.map_hexes[(hx1, hy1)]
	node2 = scenario.map_hexes[(hx2, hy2)]
	open_list = set()	# contains the nodes that may be traversed by the path
	closed_list = set()	# contains the nodes that will be traversed by the path
	start = node1
	start.h = GetHexDistance(node1.hx, node1.hy, node2.hx, node2.hy)
	start.f = start.g + start.h
	end = node2
	open_list.add(start)		# add the start node to the open list
	
	while open_list:
		
		# grab the node with the best H value from the list of open nodes
		current = sorted(open_list, key=lambda inst:inst.f)[0]
		
		# we've reached our destination
		if current == end:
			return RetracePath(current)
		
		# move this node from the open to the closed list
		open_list.remove(current)
		closed_list.add(current)
		
		# add the nodes connected to this one to the open list
		for direction in range(6):
			
			# get the hex coordinates in this direction
			hx, hy = GetAdjacentHex(current.hx, current.hy, direction)
			
			# no map hex exists here, skip
			if (hx, hy) not in scenario.map_hexes: continue
			
			node = scenario.map_hexes[(hx, hy)]
			
			# ignore nodes on closed list
			if node in closed_list: continue
			
			# ignore impassible nodes
			if node.terrain_type == 'pond': continue
			
			# check that move into this new hex would be possible for unit
			if unit is not None:
				
				# FUTURE: calculate cost of movement for this unit
				cost = 1
			
			# we're creating a path for a road
			elif road_path:
				
				# prefer to use already-existing roads
				if direction in current.dirt_roads:
					cost = -5
				
				# prefer to pass through villages if possible
				if node.terrain_type == 'village':
					cost = -2
				elif node.terrain_type == 'forest':
					cost = 4
				elif node.terrain_type == 'fields_in_season':
					cost = 2
				else:
					cost = 0
				
				if node.elevation > current.elevation:
					cost = cost * 2
				
			g = current.g + cost
			
			# if not in open list, add it
			if node not in open_list:
				node.g = g
				node.h = GetHexDistance(node.hx, node.hy, node2.hx, node2.hy)
				node.f = node.g + node.h
				node.parent = current
				open_list.add(node)
			# if already in open list, check to see if can make a better path
			else:
				if g < node.g:
					node.parent = current
					node.g = g
					node.f = node.g + node.h
	
	# no path possible
	return []


# Bresenham's Line Algorithm (based on an implementation on the roguebasin wiki)
# returns a series of x, y points along a line
# if los is true, does not include the starting location in the line
def GetLine(x1, y1, x2, y2, los=False):
	points = []
	issteep = abs(y2-y1) > abs(x2-x1)
	if issteep:
		x1, y1 = y1, x1
		x2, y2 = y2, x2
	rev = False
	if x1 > x2:
		x1, x2 = x2, x1
		y1, y2 = y2, y1
		rev = True
	deltax = x2 - x1
	deltay = abs(y2-y1)
	error = int(deltax / 2)
	y = y1
	
	if y1 < y2:
		ystep = 1
	else:
		ystep = -1
	for x in range(x1, x2 + 1):
		if issteep:
			points.append((y, x))
		else:
			points.append((x, y))
		error -= deltay
		if error < 0:
			y += ystep
			error += deltax
			
	# Reverse the list if the coordinates were reversed
	if rev:
		points.reverse()
	
	# chop off the first location if we're doing line of sight
	if los and len(points) > 1:
		points = points[1:]
	
	return points


# constrain a direction to a value 0-5
def ConstrainDir(direction):
	while direction < 0:
		direction += 6
	while direction > 5:
		direction -= 6
	return direction


# transforms an hx, hy hex location to cube coordinates
def GetCubeCoords(hx, hy):
	x = int(hx - (hy - hy&1) / 2)
	z = hy
	y = 0 - hx - z
	return (x, y, z)


# returns distance in hexes between two hexes
def GetHexDistance(hx1, hy1, hx2, hy2):
	(x1, y1, z1) = GetCubeCoords(hx1, hy1)
	(x2, y2, z2) = GetCubeCoords(hx2, hy2)
	return int((abs(x1-x2) + abs(y1-y2) + abs(z1-z2)) / 2)


# rotates a hex location around 0,0 clockwise r times
def RotateHex(hx, hy, r):
	# convert to cube coords
	(xx, yy, zz) = GetCubeCoords(hx, hy)
	for r in range(r):
		xx, yy, zz = -zz, -xx, -yy
	# convert back to hex coords
	return(int(xx + (zz - zz&1) / 2), zz)


# returns the adjacent hex in a given direction
def GetAdjacentHex(hx, hy, direction):
	(hx_mod, hy_mod) = DESTHEX[direction]
	return (hx+hx_mod, hy+hy_mod)


# returns which hexspine hx2, hy2 is along if the two hexes are along a hexspine
# otherwise returns -1
def GetHexSpine(hx1, hy1, hx2, hy2):
	# convert to cube coords
	(x1, y1, z1) = GetCubeCoords(hx1, hy1)
	(x2, y2, z2) = GetCubeCoords(hx2, hy2)
	# calculate change in values for each cube coordinate
	x = x2-x1
	y = y2-y1
	z = z2-z1
	# check cases where change would be along spine
	if x == y and z < 0: return 0
	if y == z and x > 0: return 1
	if x == z and y < 0: return 2
	if x == y and z > 0: return 3
	if y == z and x < 0: return 4
	if x == z and y > 0: return 5
	return -1


# returns arrow character used to indicate given direction
def GetDirectionalArrow(direction):
	if direction == 0:
		return chr(24)
	elif direction == 1:
		return chr(228)
	elif direction == 2:
		return chr(229)
	elif direction == 3:
		return chr(25)
	elif direction == 4:
		return chr(230)
	elif direction == 5:
		return chr(231)
	print 'ERROR: Direction not recognized: ' + str(direction)
	return ''


# return a list of hexes along a line from hex1 to hex2
# adapted from http://www.redblobgames.com/grids/hexagons/implementation.html#line-drawing
def GetHexLine(hx1, hy1, hx2, hy2):
	
	def Lerp(a, b, t):
		a = float(a)
		b = float(b)
		return a + (b - a) * t
	
	def CubeRound(x, y, z):
		rx = round(x)
		ry = round(y)
		rz = round(z)
		x_diff = abs(rx - x)
		y_diff = abs(ry - y)
		z_diff = abs(rz - z)
		if x_diff > y_diff and x_diff > z_diff:
			rx = 0 - ry - rz
		elif y_diff > z_diff:
			ry = 0 - rx - rz
		else:
			rz = 0 - rx - ry
		return (int(rx), int(ry), int(rz))

	# get cube coordinates and distance between start and end hexes
	# (repeated here from GetHexDistance because we need more than just the distance)
	(x1, y1, z1) = GetCubeCoords(hx1, hy1)
	(x2, y2, z2) = GetCubeCoords(hx2, hy2)
	distance = int((abs(x1-x2) + abs(y1-y2) + abs(z1-z2)) / 2)
	
	hex_list = []
	
	for i in range(distance+1):
		t = 1.0 / float(distance) * float(i)
		x = Lerp(x1, x2, t)
		y = Lerp(y1, y2, t)
		z = Lerp(z1, z2, t)
		(x,y,z) = CubeRound(x,y,z)
		# convert from cube to hex coordinates and add to list
		hex_list.append((x, z))

	return hex_list


# returns a ring of hexes around a center point for a given radius
# NOTE: may include hex locations that are not actually part of the game map
# FUTURE: find way to improve this function?
def GetHexRing(hx, hy, radius):
	hex_list = []
	if radius == 0: return hex_list
	# get starting point
	hx -= radius
	hy += radius
	direction = 0
	for hex_side in range(6):
		for hex_steps in range(radius):
			hex_list.append((hx, hy))
			(hx, hy) = GetAdjacentHex(hx, hy, direction)
		direction += 1
	return hex_list


# returns a rectangular area of hexes with given width and height,
#  hx, hy being the top left corner hex
def GetHexRect(hx, hy, w, h):
	hex_list = []
	for x in range(w):
		# run down hex column
		for y in range(h):
			hex_list.append((hx, hy))
			hy += 1
		# move to new column
		hy -= h
		if hx % 2 == 0:
			# even -> odd column
			direction = 2
		else:
			# odd -> even column
			direction = 1
		(hx, hy) = GetAdjacentHex(hx, hy, direction)
	return hex_list


# plot the center of a given in-game hex on the viewport console
# 0,0 appears in centre of vp console
def PlotHex(hx, hy):
	x = hx*4 + 23
	y = (hy*4) + (hx*2) + 23
	return (x+4,y+3)


# returns the direction to an adjacent hex
def GetDirectionToAdjacent(hx1, hy1, hx2, hy2):
	hx_mod = hx2 - hx1
	hy_mod = hy2 - hy1
	if (hx_mod, hy_mod) in DESTHEX:
		return DESTHEX.index((hx_mod, hy_mod))
	# hex is not adjacent
	return -1


# returns the best facing to point in the direction of the target hex
def GetDirectionToward(hx1, hy1, hx2, hy2):
	
	(x1, y1) = PlotHex(hx1, hy1)
	(x2, y2) = PlotHex(hx2, hy2)
	bearing = GetBearing(x1, y1, x2, y2)
	
	if bearing >= 330 or bearing <= 30:
		return 0
	elif bearing <= 90:
		return 1
	elif bearing >= 270:
		return 5
	elif bearing <= 150:
		return 2
	elif bearing >= 210:
		return 4
	return 3


# returns the compass bearing from x1, y1 to x2, y2
def GetBearing(x1, y1, x2, y2):
	return int((degrees(atan2((y2 - y1), (x2 - x1))) + 90.0) % 360)


# returns a bearing from 0-359 degrees
def RectifyBearing(h):
	while h < 0: h += 360
	while h > 359: h -= 360
	return h


# get the bearing from unit1 to unit2, rotated for unit1's facing
def GetRelativeBearing(unit1, unit2):
	(x1, y1) = PlotHex(unit1.hx, unit1.hy)
	(x2, y2) = PlotHex(unit2.hx, unit2.hy)
	bearing = GetBearing(x1, y1, x2, y2)
	return RectifyBearing(bearing - (unit1.facing * 60))


# get the relative facing of one unit from the point of view of another unit
# unit1 is the observer, unit2 is being observed
def GetFacing(attacker, target, turret_facing=False):
	bearing = GetRelativeBearing(target, attacker)
	if turret_facing and target.turret_facing is not None:
		bearing = RectifyBearing(bearing - (target.turret_facing * 60))
	if bearing >= 300 or bearing <= 60:
		return 'Front'
	return 'Side'


# check for an unblocked line of sight between two hexes
# returns -1.0 if no LoS, otherwise returns total terrain modifier for the line
def GetLoS(hx1, hy1, hx2, hy2):
	
	# handle the easy cases first
	
	distance = GetHexDistance(hx1, hy1, hx2, hy2)
	
	# too far away
	if distance > MAX_LOS_DISTANCE:
		return -1.0
	
	# same hex
	if hx1 == hx2 and hy1 == hy2:
		return scenario.map_hexes[(hx2, hy2)].GetTerrainMod()
	
	# adjacent hex
	if distance == 1:
		return scenario.map_hexes[(hx2, hy2)].GetTerrainMod()
	
	# store info about the starting and ending hexes for this LoS
	start_elevation = float(scenario.map_hexes[(hx1, hy1)].elevation)
	end_elevation = float(scenario.map_hexes[(hx2, hy2)].elevation)
	# calculate the slope from start to end hex
	los_slope = ((end_elevation - start_elevation) * ELEVATION_M) / (float(distance) * 160.0)
	
	# build a list of hexes along the LoS
	hex_list = []
	
	# lines of sight along hex spines need a special procedure
	mod_list = None
	hex_spine = GetHexSpine(hx1, hy1, hx2, hy2)
	if hex_spine > -1:
		mod_list = HEXSPINES[hex_spine]
		
		# start with first hex
		hx = hx1
		hy = hy1
		
		while hx != hx2 or hy != hy2:
			# break if we've gone off map
			if (hx, hy) not in scenario.map_hexes: break
			
			# emergency escape in case of stuck loop
			if libtcod.console_is_window_closed(): sys.exit()
			
			# add the next three hexes to the list
			for (xm, ym) in mod_list:
				new_hx = hx + xm
				new_hy = hy + ym
				hex_list.append((new_hx, new_hy))
			(hx, hy) = hex_list[-1]
	
	else:
		hex_list = GetHexLine(hx1, hy1, hx2, hy2)
		# remove first hex in list, since this is the observer's hex
		hex_list.pop(0)
	
	# now that we have the list of hexes along the LoS, run through them, and if an
	#   intervening hex elevation blocks the line, we can return -1
	
	# if a terrain feature intersects the line, we add its effect to the total LoS hinderance
	total_mod = 0.0
	
	# we need a few variables to temporarily store information about the first hex of
	#   a hex pair, to compare it with the second of the pair
	hexpair_floor_slope = None
	hexpair_terrain_slope = None
	hexpair_terrain_mod = None
	
	for (hx, hy) in hex_list:
		
		# hex is off map
		if (hx, hy) not in scenario.map_hexes: continue
		
		# hex is beyond the maximum LoS distance (should not happen)
		if GetHexDistance(hx1, hy1, hx, hy) > MAX_LOS_DISTANCE: return -1
		
		map_hex = scenario.map_hexes[(hx, hy)]
		elevation = (float(map_hex.elevation) - start_elevation) * ELEVATION_M
		distance = float(GetHexDistance(hx1, hy1, hx, hy))
		floor_slope = elevation / (distance * 160.0)
		terrain_slope = (elevation + TERRAIN_LOS_HEIGHT[map_hex.terrain_type]) / (distance * 160.0)
		terrain_mod = map_hex.GetTerrainMod()
		
		# if we're on a hexspine, we need to compare some pairs of hexes
		# the lowest floor slope of both hexes is used
		if mod_list is not None:
			index = hex_list.index((hx, hy))
			# hexes 0,3,6... are stored for comparison
			if index % 3 == 0:
				hexpair_floor_slope = floor_slope
				hexpair_terrain_slope = terrain_slope
				hexpair_terrain_mod = terrain_mod
				continue
			# hexes 1,4,7... are compared with stored values from other hex in pair
			elif (index - 1) % 3 == 0:
				if hexpair_floor_slope < floor_slope:
					floor_slope = hexpair_floor_slope
					terrain_slope = hexpair_terrain_slope
					terrain_mod = hexpair_terrain_mod

		# now we compare the floor slope of this hex to that of the LoS, the LoS
		# is blocked if it is higher
		if floor_slope > los_slope:
			return -1
		
		# if the terrain intervenes, then we add its modifier to the total
		if terrain_slope > los_slope:
			total_mod += terrain_mod
			# if total modifier is too high, LoS is blocked
			if total_mod > MAX_LOS_MOD:
				return -1.0

	return total_mod


# wait for a specified amount of miliseconds, refreshing the screen in the meantime
def Wait(wait_time):
	wait_time = wait_time * 0.01
	start_time = time.time()
	while time.time() - start_time < wait_time:
	
		# added this to avoid the spinning wheel of death in Windows
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,
			key, mouse)
		if libtcod.console_is_window_closed(): sys.exit()
			
		libtcod.console_flush()


# wait for player to press enter before continuing
# option to allow backspace pressed instead, returns True if so 
def WaitForEnter(allow_cancel=False):
	end_pause = False
	cancel = False
	while not end_pause:
		# get input from user
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,
			key, mouse)
		
		# emergency exit from game
		if libtcod.console_is_window_closed(): sys.exit()
		
		elif key.vk == libtcod.KEY_ENTER: 
			end_pause = True
		
		elif key.vk == libtcod.KEY_BACKSPACE and allow_cancel:
			end_pause = True
			cancel = True
		
		# refresh the screen
		libtcod.console_flush()
	
	if allow_cancel and cancel:
		return True
	return False


# save the current game in progress
def SaveGame():
	save = shelve.open('savegame', 'n')
	# TEMP - move to session object in future
	scenario.ClearHexConsoles()
	save['scenario'] = scenario
	save.close()
	scenario.GenerateHexConsoles()


# load a saved game
def LoadGame():
	global scenario
	save = shelve.open('savegame')
	scenario = save['scenario']
	save.close()
	scenario.GenerateHexConsoles()


# remove a saved game, either because the scenario is over or the player abandoned it
def EraseGame():
	os.remove('savegame')


##########################################################################################
#                                     In-Game Menu                                       #
##########################################################################################

# display the game menu to screen, with the given tab active

def ShowGameMenu(active_tab):
	
	# darken screen background
	libtcod.console_blit(darken_con, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.7)
	
	# blit menu background to game menu console
	libtcod.console_blit(game_menu_bkg, 0, 0, 0, 0, game_menu_con, 0, 0)
	
	# fill in active tab info
	# TEMP - only game menu tab possible for now
	libtcod.console_set_default_foreground(game_menu_con, libtcod.light_blue)
	libtcod.console_print(game_menu_con, 25, 22, 'Esc')
	libtcod.console_print(game_menu_con, 25, 24, 'Q')
	libtcod.console_print(game_menu_con, 25, 25, 'A')
	
	libtcod.console_set_default_foreground(game_menu_con, libtcod.lighter_grey)
	libtcod.console_print(game_menu_con, 30, 22, 'Return to Game')
	libtcod.console_print(game_menu_con, 30, 24, 'Save and Quit to Main Menu')
	libtcod.console_print(game_menu_con, 30, 25, 'Abandon Game')
	
	# blit menu to screen
	libtcod.console_blit(game_menu_con, 0, 0, 0, 0, 0, 3, 3)
	libtcod.console_flush()
	Wait(15)
	
	# get input from player
	exit_menu = False
	while not exit_menu:
		libtcod.console_flush()
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,
			key, mouse)
		if libtcod.console_is_window_closed(): sys.exit()
		
		if key is None: continue
		
		# exit menu
		if key.vk == libtcod.KEY_ESCAPE:
			return ''
		
		key_char = chr(key.c).lower()
		
		if key_char == 'q':
			SaveGame()
			return 'exit_game'
		
		elif key_char == 'a':
			text = 'Abandoning will erase the saved game.'
			result = ShowNotification(text, confirm=True)
			if result:
				EraseGame()
				return 'exit_game'
			libtcod.console_blit(game_menu_con, 0, 0, 0, 0, 0, 3, 3)
			libtcod.console_flush()
			Wait(15)



##########################################################################################
#                              Console Drawing Functions                                 #
##########################################################################################


# draw an ArmCom2-style frame to the given console
def DrawFrame(console, x, y, w, h):
	libtcod.console_put_char(console, x, y, 249)
	libtcod.console_put_char(console, x+w-1, y, 249)
	libtcod.console_put_char(console, x, y+h-1, 249)
	libtcod.console_put_char(console, x+w-1, y+h-1, 249)
	for x1 in range(x+1, x+w-1):
		libtcod.console_put_char(console, x1, y, 196)
		libtcod.console_put_char(console, x1, y+h-1, 196)
	for y1 in range(y+1, y+h-1):
		libtcod.console_put_char(console, x, y1, 179)
		libtcod.console_put_char(console, x+w-1, y1, 179)


# display a pop-up message on the root console
# can be used for yes/no confirmation
def ShowNotification(text, confirm=False):
	
	# determine window x, height, and y position
	x = WINDOW_XM - 30
	lines = wrap(text, 58)
	h = len(lines) + 6
	y = WINDOW_YM - int(h/2)
	
	# create a local copy of the current screen to re-draw when we're done
	temp_con = libtcod.console_new(WINDOW_WIDTH, WINDOW_HEIGHT)
	libtcod.console_blit(0, 0, 0, 0, 0, temp_con, 0, 0)
	
	# darken background 
	libtcod.console_blit(darken_con, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.5)
	
	# draw a black rect and an outline
	libtcod.console_rect(0, x, y, 60, h, True, libtcod.BKGND_SET)
	DrawFrame(0, x, y, 60, h)
	
	# display message
	ly = y+2
	for line in lines:
		libtcod.console_print(0, x+2, ly, line)
		ly += 1
	
	# if asking for confirmation, display yes/no choices, otherwise display a simple messages
	if confirm:
		text = 'Proceed? Y/N'
	else:
		text = 'Enter to Continue'
	
	libtcod.console_print_ex(0, WINDOW_XM, y+h-2, libtcod.BKGND_NONE, libtcod.CENTER,
		text)
	
	# show to screen
	libtcod.console_flush()
	Wait(15)
	
	exit_menu = False
	while not exit_menu:
		libtcod.console_flush()
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,
			key, mouse)
		if libtcod.console_is_window_closed(): sys.exit()
		
		if key is None: continue
		
		if confirm:
			key_char = chr(key.c).lower()
			
			if key_char == 'y':
				# restore original screen before returning
				libtcod.console_blit(temp_con, 0, 0, 0, 0, 0, 0, 0)
				del temp_con
				return True
			elif key_char == 'n':
				libtcod.console_blit(temp_con, 0, 0, 0, 0, 0, 0, 0)
				del temp_con
				return False
		else:
			if key.vk == libtcod.KEY_ENTER:
				exit_menu = True
	
	libtcod.console_blit(temp_con, 0, 0, 0, 0, 0, 0, 0)
	del temp_con
	

# draw the map viewport console
# each hex is 5x5 cells, but edges overlap with adjacent hexes
def UpdateVPCon():

	libtcod.console_set_default_background(map_vp_con, libtcod.black)
	libtcod.console_clear(map_vp_con)
	libtcod.console_clear(fov_con)
	scenario.hex_map_index = {}
	
	# draw off-map hexes first
	for (hx, hy), (map_hx, map_hy) in scenario.map_vp.items():
		if (map_hx, map_hy) not in scenario.map_hexes:
			(x,y) = PlotHex(hx, hy)
			libtcod.console_blit(tile_offmap, 0, 0, 0, 0, map_vp_con, x-3, y-2)
	
	for elevation in range(4):
		for (hx, hy) in VP_HEXES:
			(map_hx, map_hy) = scenario.map_vp[(hx, hy)]
			if (map_hx, map_hy) not in scenario.map_hexes:
				continue
			map_hex = scenario.map_hexes[(map_hx, map_hy)]
			
			if map_hex.elevation != elevation: continue
			(x,y) = PlotHex(hx, hy)
			
			libtcod.console_blit(scenario.hex_consoles[map_hex.terrain_type][map_hex.elevation],
				0, 0, 0, 0, map_vp_con, x-3, y-2)
			
			# if this hex is visible, unmask it in the FoV mask
			if (map_hx, map_hy) in scenario.player_unit.fov:
				libtcod.console_blit(hex_fov, 0, 0, 0, 0, fov_con, x-3, y-2)
				
			# record map hexes of screen locations
			for x1 in range(x-1, x+2):
				scenario.hex_map_index[(x1,y-1)] = (map_hx, map_hy)
				scenario.hex_map_index[(x1,y+1)] = (map_hx, map_hy)
			for x1 in range(x-2, x+3):
				scenario.hex_map_index[(x1,y)] = (map_hx, map_hy)
	
	# draw roads overtop
	for (hx, hy) in VP_HEXES:
		(map_hx, map_hy) = scenario.map_vp[(hx, hy)]
		if (map_hx, map_hy) not in scenario.map_hexes:
			continue
		map_hex = scenario.map_hexes[(map_hx, map_hy)]
		# no road here
		if len(map_hex.dirt_roads) == 0: continue
		for direction in map_hex.dirt_roads:
			
			# get other VP hex linked by road
			(hx2, hy2) = GetAdjacentHex(hx, hy, ConstrainDir(direction - scenario.player_unit.facing))
			
			# only draw if it is in direction 0-2, unless the other hex is off the VP
			if (hx2, hy2) in VP_HEXES and 3 <= direction <= 5: continue
			
			# paint road
			(x1, y1) = PlotHex(hx, hy)
			(hx2, hy2) = GetAdjacentHex(hx, hy, ConstrainDir(direction - scenario.player_unit.facing))
			(x2, y2) = PlotHex(hx2, hy2)
			line = GetLine(x1, y1, x2, y2)
			for (x, y) in line:
				
				# don't paint over outside of map area
				if libtcod.console_get_char_background(map_vp_con, x, y) == libtcod.black:
					continue
				
				libtcod.console_set_char_background(map_vp_con, x, y,
					DIRT_ROAD_COL, libtcod.BKGND_SET)
				
				# if character is not blank or hex edge, remove it
				if libtcod.console_get_char(map_vp_con, x, y) not in [0, 250]:
					libtcod.console_set_char(map_vp_con, x, y, 0)
			
	
	# highlight objective hexes
	for (hx, hy) in VP_HEXES:
		(map_hx, map_hy) = scenario.map_vp[(hx, hy)]
		if (map_hx, map_hy) not in scenario.map_hexes: continue
		map_hex = scenario.map_hexes[(map_hx, map_hy)]
		if map_hex.objective is not None:
			(x,y) = PlotHex(hx, hy)
			libtcod.console_blit(hex_objective_neutral, 0, 0, 0, 0,
				map_vp_con, x-3, y-2, 1.0, 0.0)
			

# display units on the unit console
# also displays map hex highlight and LoS if any
def UpdateUnitCon():
	libtcod.console_clear(unit_con)
	
	# run through each viewport hex
	for (vp_hx, vp_hy) in VP_HEXES:
		# determine which map hex this viewport hex displays
		(map_hx, map_hy) = scenario.map_vp[(vp_hx, vp_hy)]
		# hex is off-map
		if (map_hx, map_hy) not in scenario.map_hexes: continue
		# hex not visible to player
		#if (map_hx, map_hy) not in scenario.player_unit.fov: continue
		# get the map hex
		map_hex = scenario.map_hexes[(map_hx, map_hy)]
		
		# any units in the stack
		if len(map_hex.unit_stack) != 0:
			# display the top unit in the stack
			map_hex.unit_stack[0].DrawMe(vp_hx, vp_hy)
	
		# check for hex highlight if any
		if scenario.highlighted_hex is not None:
			if scenario.highlighted_hex == (map_hx, map_hy):
				(x,y) = PlotHex(vp_hx, vp_hy)
				libtcod.console_put_char_ex(unit_con, x-1, y-1, 169, libtcod.cyan,
					libtcod.black)
				libtcod.console_put_char_ex(unit_con, x+1, y-1, 170, libtcod.cyan,
					libtcod.black)
				libtcod.console_put_char_ex(unit_con, x-1, y+1, 28, libtcod.cyan,
					libtcod.black)
				libtcod.console_put_char_ex(unit_con, x+1, y+1, 29, libtcod.cyan,
					libtcod.black)
		
	# display LoS if applicable
	if scenario.player_los_active and scenario.player_target is not None:
		line = GetLine(scenario.player_unit.screen_x, scenario.player_unit.screen_y,
			scenario.player_target.screen_x, scenario.player_target.screen_y)
		for (x,y) in line[2:-1]:
			libtcod.console_put_char_ex(unit_con, x, y, 250, libtcod.red,
				libtcod.black)


# display information about the player unit
def UpdatePlayerInfoCon():
	libtcod.console_set_default_background(player_info_con, libtcod.black)
	libtcod.console_clear(player_info_con)
	
	unit = scenario.player_unit
	
	libtcod.console_set_default_foreground(player_info_con, libtcod.lighter_blue)
	libtcod.console_print(player_info_con, 0, 0, unit.unit_id)
	libtcod.console_set_default_foreground(player_info_con, libtcod.light_grey)
	libtcod.console_print(player_info_con, 0, 1, unit.GetStat('class'))
	portrait = unit.GetStat('portrait')
	if portrait is not None:
		libtcod.console_blit(LoadXP(portrait), 0, 0, 0, 0, player_info_con, 0, 2)
	
	# weapons
	libtcod.console_set_default_foreground(player_info_con, libtcod.white)
	libtcod.console_set_default_background(player_info_con, libtcod.darkest_red)
	libtcod.console_rect(player_info_con, 0, 10, 24, 2, True, libtcod.BKGND_SET)
	
	text = ''
	for weapon in unit.weapon_list:
		if text != '':
			text += ', '
		text += weapon.stats['name']
	lines = wrap(text, 24)
	y = 10
	for line in lines:
		libtcod.console_print(player_info_con, 0, y, line)
		y += 1
		if y == 12: break
	
	# armour
	armour = unit.GetStat('armour')
	if armour is None:
		libtcod.console_print(player_info_con, 0, 12, 'Unarmoured')
	else:
		libtcod.console_print(player_info_con, 0, 12, 'Armoured')
		libtcod.console_set_default_foreground(player_info_con, libtcod.light_grey)
		if unit.GetStat('turret'):
			text = 'T'
		else:
			text = 'U'
		text += ' ' + armour['turret_front'] + '/' + armour['turret_side']
		libtcod.console_print(player_info_con, 1, 13, text)
		text = 'H ' + armour['hull_front'] + '/' + armour['hull_side']
		libtcod.console_print(player_info_con, 1, 14, text)
	
	# movement
	libtcod.console_set_default_foreground(player_info_con, libtcod.light_green)
	libtcod.console_print_ex(player_info_con, 23, 12, libtcod.BKGND_NONE, libtcod.RIGHT,
		unit.GetStat('movement_class'))
	
	# status
	libtcod.console_set_default_foreground(player_info_con, libtcod.light_grey)
	libtcod.console_set_default_background(player_info_con, libtcod.darkest_blue)
	libtcod.console_rect(player_info_con, 0, 15, 24, 3, True, libtcod.BKGND_SET)
	
	if unit.moved:
		libtcod.console_print(player_info_con, 0, 16, 'Moved')
	if unit.fired:
		libtcod.console_print(player_info_con, 6, 16, 'Fired')


# list player unit crew positions and current crewmen if any
def UpdateCrewPositionCon():
	libtcod.console_clear(crew_position_con)
	
	unit = scenario.player_unit
	
	if len(unit.crew_positions) == 0:
		return
	
	y = 1
	for position in unit.crew_positions:
		
		# highlight if special action phase and this crewman is selected
		if scenario.game_turn['current_phase'] == 'Crew Actions':
			if unit.crew_positions.index(position) == scenario.selected_position:
				libtcod.console_set_default_background(crew_position_con, libtcod.darker_blue)
				libtcod.console_rect(crew_position_con, 0, y, 24, 4, True, libtcod.BKGND_SET)
				libtcod.console_set_default_background(crew_position_con, libtcod.black)
		
		libtcod.console_set_default_foreground(crew_position_con, libtcod.light_blue)
		libtcod.console_print(crew_position_con, 0, y, position.name)
		libtcod.console_set_default_foreground(crew_position_con, libtcod.white)
		libtcod.console_print_ex(crew_position_con, 23, y, libtcod.BKGND_NONE, 
			libtcod.RIGHT, position.location)
		if not position.hatch:
			text = '--'
		else:
			if position.hatch_open:
				text = 'CE'
			else:
				text = 'BU'
		libtcod.console_print_ex(crew_position_con, 23, y+1, libtcod.BKGND_NONE, 
			libtcod.RIGHT, text)
		
		if position.crewman is None:
			text = 'Empty'
		else:
			(firstname, surname) = position.crewman.name
			text = firstname[0] + '. ' + surname
		
		# names might have special characters so we encode it before printing it
		libtcod.console_print(crew_position_con, 0, y+1, text.encode('IBM850'))
		
		# special action if any
		if position.crewman is not None:
			if position.crewman.current_action is not None:
				libtcod.console_set_default_foreground(crew_position_con,
					libtcod.dark_yellow)
				libtcod.console_print(crew_position_con, 0, y+2,
					position.crewman.current_action)
				libtcod.console_set_default_foreground(crew_position_con,
					libtcod.white)
		
		y += 5


# list current player commands
def UpdateCommandCon():
	libtcod.console_clear(command_con)
	libtcod.console_set_default_foreground(command_con, libtcod.white)
	
	if scenario.game_turn['current_phase'] == 'Crew Actions':
		libtcod.console_set_default_background(command_con, libtcod.darker_yellow)
		libtcod.console_rect(command_con, 0, 0, 24, 1, True, libtcod.BKGND_SET)
		libtcod.console_set_default_background(command_con, libtcod.black)
		libtcod.console_print_ex(command_con, 12, 0, libtcod.BKGND_NONE, libtcod.CENTER,
			'Crew Actions')
		
		if scenario.game_turn['active_player'] != 0: return
		
		libtcod.console_set_default_foreground(command_con, libtcod.light_blue)
		libtcod.console_print(command_con, 2, 2, 'I/K')
		libtcod.console_print(command_con, 2, 3, 'J/L')
		libtcod.console_print(command_con, 2, 4, 'H')
		
		libtcod.console_set_default_foreground(command_con, libtcod.lighter_grey)
		libtcod.console_print(command_con, 9, 2, 'Select Crew')
		libtcod.console_print(command_con, 9, 3, 'Set Action')
		libtcod.console_print(command_con, 9, 4, 'Toggle Hatch')
	
	elif scenario.game_turn['current_phase'] == 'Spotting':
		
		libtcod.console_set_default_background(command_con, libtcod.darker_purple)
		libtcod.console_rect(command_con, 0, 0, 24, 1, True, libtcod.BKGND_SET)
		libtcod.console_set_default_background(command_con, libtcod.black)
		libtcod.console_print_ex(command_con, 12, 0, libtcod.BKGND_NONE, libtcod.CENTER,
			'Spotting')
		
		if scenario.game_turn['active_player'] != 0: return
	
	elif scenario.game_turn['current_phase'] == 'Movement':
	
		libtcod.console_set_default_background(command_con, libtcod.darker_green)
		libtcod.console_rect(command_con, 0, 0, 24, 1, True, libtcod.BKGND_SET)
		libtcod.console_set_default_background(command_con, libtcod.black)
		libtcod.console_print_ex(command_con, 12, 0, libtcod.BKGND_NONE, libtcod.CENTER,
			'Movement')
		
		if scenario.game_turn['active_player'] != 0: return
		
		libtcod.console_set_default_foreground(command_con, libtcod.light_blue)
		libtcod.console_print(command_con, 2, 2, 'W')
		libtcod.console_print(command_con, 2, 3, 'A/D')
		
		
		libtcod.console_set_default_foreground(command_con, libtcod.lighter_grey)
		libtcod.console_print(command_con, 9, 2, 'Move Forward')
		libtcod.console_print(command_con, 9, 3, 'Pivot Hull')
		
	
	elif scenario.game_turn['current_phase'] == 'Combat':
		
		libtcod.console_set_default_background(command_con, libtcod.darker_red)
		libtcod.console_rect(command_con, 0, 0, 24, 1, True, libtcod.BKGND_SET)
		libtcod.console_set_default_background(command_con, libtcod.black)
		libtcod.console_print_ex(command_con, 12, 0, libtcod.BKGND_NONE, libtcod.CENTER,
			'Combat')
		
		if scenario.game_turn['active_player'] != 0: return
		
		libtcod.console_set_default_foreground(command_con, libtcod.light_blue)
		# TEMP - hidden since no additional weapons have been added yet
		#libtcod.console_print(command_con, 2, 2, 'W/S')
		libtcod.console_print(command_con, 2, 3, 'Q/E')
		libtcod.console_print(command_con, 2, 4, 'A/D')
		libtcod.console_print(command_con, 2, 5, 'F')
		
		libtcod.console_set_default_foreground(command_con, libtcod.lighter_grey)
		# TEMP - hidden since no additional weapons have been added yet
		#libtcod.console_print(command_con, 9, 2, 'Select Weapon')
		libtcod.console_print(command_con, 9, 3, 'Rotate Turret')
		libtcod.console_print(command_con, 9, 4, 'Select Target')
		libtcod.console_print(command_con, 9, 5, 'Fire')
		
	libtcod.console_set_default_foreground(command_con, libtcod.light_blue)
	libtcod.console_print(command_con, 2, 11, 'Enter')
	libtcod.console_set_default_foreground(command_con, libtcod.lighter_grey)
	libtcod.console_print(command_con, 9, 11, 'Next Phase')
	
	
# draw information about the hex currently under the mouse cursor to the hex terrain info
# console, 16x10
def UpdateHexTerrainCon():
	libtcod.console_clear(hex_terrain_con)
	
	# mouse cursor outside of map area
	if mouse.cx < 32: return
	x = mouse.cx - 31
	y = mouse.cy - 4
	if (x,y) not in scenario.hex_map_index: return
	
	libtcod.console_set_default_foreground(hex_terrain_con, libtcod.white)
	
	(hx, hy) = scenario.hex_map_index[(x,y)]
	map_hex = scenario.map_hexes[(hx, hy)]
	text = HEX_TERRAIN_DESC[map_hex.terrain_type]
	libtcod.console_print(hex_terrain_con, 0, 0, text)
	
	# TEMP
	libtcod.console_print(hex_terrain_con, 0, 1, str(hx) + ',' + str(hy))
	text = str(map_hex.elevation * ELEVATION_M) + ' m.'
	libtcod.console_print_ex(hex_terrain_con, 15, 1, libtcod.BKGND_NONE,
		libtcod.RIGHT, text)
	
	if map_hex.objective is not None:
		libtcod.console_set_default_foreground(hex_terrain_con, libtcod.light_blue)
		libtcod.console_print(hex_terrain_con, 0, 2, 'Objective')
		if map_hex.objective == -1:
			return
		if map_hex.objective == 0:
			text = 'Player Held'
		else:
			text = 'Enemy Held'
		libtcod.console_set_default_foreground(hex_terrain_con, libtcod.white)
		libtcod.console_print(hex_terrain_con, 0, 3, text)
	
	if len(map_hex.dirt_roads) > 0:
		libtcod.console_print(hex_terrain_con, 0, 9, 'Dirt Road')


# draw information based on current turn phase to contextual info console
def UpdateContextCon():
	libtcod.console_clear(context_con)
	
	if scenario.game_turn['active_player'] != 0:
		return
	
	libtcod.console_set_default_foreground(context_con, libtcod.white)
	
	if scenario.game_turn['current_phase'] == 'Crew Actions':
		position = scenario.player_unit.crew_positions[scenario.selected_position]
		action = position.crewman.current_action
		
		if action is None:
			libtcod.console_print(context_con, 0, 0, 'No action')
			libtcod.console_print(context_con, 0, 1, 'assigned')
		else:
			libtcod.console_set_default_foreground(context_con,
				libtcod.dark_yellow)
			libtcod.console_print(context_con, 0, 0, action)
			libtcod.console_set_default_foreground(context_con,
				libtcod.light_grey)
			
			# TEMP - need this to avoid crash when non-special actions are displayed
			if 'desc' not in CREW_ACTIONS[action]:
				lines = []
			else:
				lines = wrap(CREW_ACTIONS[action]['desc'], 16)
			y = 2
			for line in lines:
				libtcod.console_print(context_con, 0, y, line)
				y += 1
				if y == 9: break
	
	elif scenario.game_turn['current_phase'] == 'Movement':
		
		libtcod.console_set_default_foreground(context_con, libtcod.light_green)
		libtcod.console_print(context_con, 0, 0, scenario.player_unit.GetStat('movement_class'))
		
		libtcod.console_set_default_foreground(context_con, libtcod.light_grey)
		if scenario.player_unit.move_finished:
			libtcod.console_print(context_con, 0, 2, 'Move finished')
			return
		
		# display chance of getting a bonus move
		(hx, hy) = GetAdjacentHex(scenario.player_unit.hx, scenario.player_unit.hy,
			scenario.player_unit.facing)
		
		# off map
		if (hx, hy) not in scenario.map_hexes: return
		
		# display destination terrain type
		text = HEX_TERRAIN_DESC[scenario.map_hexes[(hx, hy)].terrain_type]
		libtcod.console_print(context_con, 0, 2, text)
		
		# display road status if any
		if scenario.player_unit.facing in scenario.map_hexes[(scenario.player_unit.hx, scenario.player_unit.hy)].dirt_roads:
			libtcod.console_print(context_con, 0, 3, '+Dirt Road')
		
		# get bonus move chance
		libtcod.console_print(context_con, 0, 4, '+1 move chance:')
		chance = round(scenario.CalcBonusMove(scenario.player_unit, hx, hy), 2)
		libtcod.console_print(context_con, 1, 5, str(chance) + '%%')
	
	elif scenario.game_turn['current_phase'] == 'Combat':
		if scenario.selected_weapon is not None:
			libtcod.console_set_default_background(context_con, libtcod.darkest_red)
			libtcod.console_rect(context_con, 0, 0, 16, 1, True, libtcod.BKGND_SET)
			libtcod.console_print(context_con, 0, 0, scenario.selected_weapon.stats['name'])
			libtcod.console_set_default_background(context_con, libtcod.darkest_grey)
			
			# update attack description is case changes occured since last phase
			if scenario.player_target is not None:
				scenario.player_attack_desc = scenario.CheckAttack(scenario.player_unit,
					scenario.selected_weapon, scenario.player_target)

		if scenario.player_attack_desc != '':
			libtcod.console_set_default_foreground(context_con, libtcod.red)
			lines = wrap(scenario.player_attack_desc, 16)
			y = 7
			for line in lines[:3]:
				libtcod.console_print(context_con, 0, y, line)
				y += 1
			libtcod.console_set_default_foreground(context_con, libtcod.light_grey)



# display information about an on-map unit under the mouse cursor, 16x10
def UpdateUnitInfoCon():
	libtcod.console_clear(unit_info_con)
	
	# mouse cursor outside of map area
	if mouse.cx < 32: return
	x = mouse.cx - 31
	y = mouse.cy - 4
	if (x,y) not in scenario.hex_map_index: return
	
	(hx, hy) = scenario.hex_map_index[(x,y)]
	
	unit_stack = scenario.map_hexes[(hx, hy)].unit_stack
	if len(unit_stack) == 0: return
	
	# display unit info
	unit = unit_stack[0]
	if unit.owning_player == 1:
		if not unit.known:
			libtcod.console_set_default_foreground(unit_info_con, UNKNOWN_UNIT_COL)
			libtcod.console_print(unit_info_con, 0, 0, 'Possible Enemy')
			return
		else:
			col = ENEMY_UNIT_COL
	else:	
		col = libtcod.white
	
	libtcod.console_set_default_foreground(unit_info_con, col)
	lines = wrap(unit.unit_id, 16)
	y = 0
	for line in lines[:2]:
		libtcod.console_print(unit_info_con, 0, y, line)
		y+=1
	libtcod.console_set_default_foreground(unit_info_con, libtcod.light_grey)
	libtcod.console_print(unit_info_con, 0, 2, unit.GetStat('class'))


# update objective info console, 16x10
def UpdateObjectiveInfoCon():
	libtcod.console_clear(objective_con)
	libtcod.console_set_default_foreground(objective_con, libtcod.light_blue)
	libtcod.console_print(objective_con, 0, 0, 'Objectives')
	libtcod.console_set_default_foreground(objective_con, libtcod.light_grey)
	libtcod.console_print(objective_con, 0, 1, '----------------')
	y = 2
	for map_hex in scenario.map_objectives:
		distance = GetHexDistance(scenario.player_unit.hx, scenario.player_unit.hy,
			map_hex.hx, map_hex.hy) * 160
		if distance > 1000:
			text = str(float(distance) / 1000.0) + ' km.'
		else:
			text = str(distance) + ' m.'
		libtcod.console_print_ex(objective_con, 13, y, libtcod.BKGND_NONE,
			libtcod.RIGHT, text)
		
		# capture status
		if map_hex.objective == 0:
			char = 251
		else:
			char = 120
		libtcod.console_put_char(objective_con, 0, y, char)
		
		# directional arrow if required
		if distance > 0:
			direction = GetDirectionToward(scenario.player_unit.hx, scenario.player_unit.hy,
				map_hex.hx, map_hex.hy)
			direction = ConstrainDir(direction + (0 - scenario.player_unit.facing))
			libtcod.console_put_char(objective_con, 15, y, GetDirectionalArrow(direction))
		y += 2
	

# draw all layers of scenario display to screen
def UpdateScenarioDisplay():
	libtcod.console_clear(con)
	libtcod.console_blit(bkg_console, 0, 0, 0, 0, con, 0, 0)		# grey outline
	libtcod.console_blit(player_info_con, 0, 0, 0, 0, con, 1, 1)		# player unit info
	libtcod.console_blit(crew_position_con, 0, 0, 0, 0, con, 1, 20)		# crew position info
	libtcod.console_blit(command_con, 0, 0, 0, 0, con, 1, 47)		# player commands
	
	# map viewport layers
	libtcod.console_blit(map_vp_con, 0, 0, 0, 0, con, 31, 4)		# map viewport
	libtcod.console_blit(fov_con, 0, 0, 0, 0, con, 31, 4, FOV_SHADE, FOV_SHADE)	# player FoV layer
	libtcod.console_blit(unit_con, 0, 0, 0, 0, con, 31, 4, 1.0, 0.0)	# unit layer
	
	# informational consoles surrounding the map viewport
	libtcod.console_blit(context_con, 0, 0, 0, 0, con, 27, 1)		# contextual info
	libtcod.console_blit(unit_info_con, 0, 0, 0, 0, con, 27, 50)		# unit info
	libtcod.console_blit(objective_con, 0, 0, 0, 0, con, 74, 1)		# target info
	libtcod.console_blit(hex_terrain_con, 0, 0, 0, 0, con, 74, 50)		# hex terrain info
	
	# TEMP - draw current active player and time directly to console
	if scenario.game_turn['active_player'] == 0:
		text = 'Player'
	else:
		text = 'Enemy'
	text += ' Turn ' + str(scenario.game_turn['turn_number'])
	libtcod.console_print_ex(con, 58, 0, libtcod.BKGND_NONE, libtcod.CENTER,
		text)
	text = str(scenario.game_turn['hour']) + ':' + str(scenario.game_turn['minute']).zfill(2)
	libtcod.console_print_ex(con, 58, 1, libtcod.BKGND_NONE, libtcod.CENTER,
		text)
	
	libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
	

##########################################################################################
#                                 Main Scenario Loop                                     #
##########################################################################################

def DoScenario(load_game=False):
	
	global scenario
	global bkg_console, map_vp_con, unit_con, player_info_con, hex_terrain_con
	global crew_position_con, command_con, context_con, unit_info_con, objective_con
	global attack_con, fov_con, hex_fov, popup_bkg, hex_objective_neutral
	global tile_offmap
	
	# set up consoles
	
	# background outline console for left column
	bkg_console = LoadXP('bkg.xp')
	# black mask for map tiles not visible to player
	hex_fov = LoadXP('hex_fov.xp')
	libtcod.console_set_key_color(hex_fov, libtcod.black)
	# background for scenario message window
	popup_bkg = LoadXP('popup_bkg.xp')
	# highlight for objective hexes
	hex_objective_neutral = LoadXP('hex_objective_neutral.xp')
	libtcod.console_set_key_color(hex_objective_neutral, KEY_COLOR)
	
	# map viewport console
	map_vp_con = libtcod.console_new(55, 53)
	libtcod.console_set_default_background(map_vp_con, libtcod.black)
	libtcod.console_set_default_foreground(map_vp_con, libtcod.white)
	libtcod.console_clear(map_vp_con)
	
	# indicator for off-map tiles on viewport
	tile_offmap = LoadXP('tile_offmap.xp')
	libtcod.console_set_key_color(tile_offmap, KEY_COLOR)
	
	# unit layer console
	unit_con = libtcod.console_new(55, 53)
	libtcod.console_set_default_background(unit_con, KEY_COLOR)
	libtcod.console_set_default_foreground(unit_con, libtcod.white)
	libtcod.console_set_key_color(unit_con, KEY_COLOR)
	libtcod.console_clear(unit_con)
	
	# player Field of View mask console
	fov_con = libtcod.console_new(55, 53)
	libtcod.console_set_default_background(fov_con, libtcod.black)
	libtcod.console_set_default_foreground(fov_con, libtcod.black)
	libtcod.console_set_key_color(fov_con, KEY_COLOR)
	libtcod.console_clear(fov_con)
	
	# player info console
	player_info_con = libtcod.console_new(24, 18)
	libtcod.console_set_default_background(player_info_con, libtcod.black)
	libtcod.console_set_default_foreground(player_info_con, libtcod.white)
	libtcod.console_clear(player_info_con)
	
	# crew position console
	crew_position_con = libtcod.console_new(24, 26)
	libtcod.console_set_default_background(crew_position_con, libtcod.black)
	libtcod.console_set_default_foreground(crew_position_con, libtcod.white)
	libtcod.console_clear(crew_position_con)
	
	# player command console
	command_con = libtcod.console_new(24, 12)
	libtcod.console_set_default_background(command_con, libtcod.black)
	libtcod.console_set_default_foreground(command_con, libtcod.white)
	libtcod.console_clear(command_con)
	
	# hex terrain info console
	hex_terrain_con = libtcod.console_new(16, 10)
	libtcod.console_set_default_background(hex_terrain_con, libtcod.darkest_grey)
	libtcod.console_set_default_foreground(hex_terrain_con, libtcod.white)
	libtcod.console_clear(hex_terrain_con)
	
	# unit info console
	unit_info_con = libtcod.console_new(16, 10)
	libtcod.console_set_default_background(unit_info_con, libtcod.darkest_grey)
	libtcod.console_set_default_foreground(unit_info_con, libtcod.white)
	libtcod.console_clear(unit_info_con)
	
	# contextual info console
	context_con = libtcod.console_new(16, 10)
	libtcod.console_set_default_background(context_con, libtcod.darkest_grey)
	libtcod.console_set_default_foreground(context_con, libtcod.white)
	libtcod.console_clear(context_con)
	
	# objective info console
	objective_con = libtcod.console_new(16, 10)
	libtcod.console_set_default_background(objective_con, libtcod.darkest_grey)
	libtcod.console_set_default_foreground(objective_con, libtcod.white)
	libtcod.console_clear(objective_con)
	
	# attack display console
	attack_con = libtcod.console_new(26, 60)
	libtcod.console_set_default_background(attack_con, libtcod.black)
	libtcod.console_set_default_foreground(attack_con, libtcod.white)
	libtcod.console_clear(attack_con)
	
	# load a saved game or start a new game
	if load_game:
		LoadGame()
	else:
	
		# generate a new scenario object and generate terrain for the hex map
		scenario = Scenario()
		scenario.GenerateTerrain()
		
		# set up time of day and current phase
		scenario.game_turn['hour'] = 5
		scenario.game_turn['current_phase'] = PHASE_LIST[0]
		
		# generate scenario units
		
		# player tank
		new_unit = Unit('Panzer 38(t) A')
		new_unit.owning_player = 0
		new_unit.nation = 'Germany'
		new_unit.hy = 12
		new_unit.facing = 0
		new_unit.turret_facing = 0
		
		# add this unit to the hex stack
		# FUTURE: integrate into a spawn unit function
		scenario.map_hexes[(new_unit.hx, new_unit.hy)].unit_stack.append(new_unit)
		
		# generate a new crew for this unit
		new_unit.GenerateNewCrew()
		
		scenario.units.append(new_unit)
		scenario.player_unit = new_unit
		
		new_unit.CalcFoV()
		
		# enemy units
		for i in range(2):
		
			new_unit = Unit('7TP')
			new_unit.owning_player = 1
			new_unit.ai = AI(new_unit)
			new_unit.nation = 'Poland'
			new_unit.facing = 3
			new_unit.turret_facing = 3
			new_unit.GenerateNewCrew()
			scenario.units.append(new_unit)
			
			new_unit = Unit('Vickers 6-Ton Mark E')
			new_unit.owning_player = 1
			new_unit.ai = AI(new_unit)
			new_unit.nation = 'Poland'
			new_unit.facing = 3
			new_unit.turret_facing = 3
			new_unit.GenerateNewCrew()
			scenario.units.append(new_unit)
		
		# set dummy enemy units
		# TEMP - should be approx 1/4 of total enemy units
		dummy_units = 2
		unit_list = []
		for unit in scenario.units:
			if unit.owning_player == 1:
				unit_list.append(unit)
		unit_list = sample(unit_list, dummy_units)	
		for unit in unit_list:
			unit.dummy = True
		
		# TEMP - place enemy units randomly
		for unit in scenario.units:
			if unit.owning_player == 0: continue
			for tries in range(300):
				(hx, hy) = choice(scenario.map_hexes.keys())
				
				# terrain is not passable
				if scenario.map_hexes[(hx, hy)].terrain_type == 'pond':
					continue
				
				if GetHexDistance(hx, hy, scenario.player_unit.hx, scenario.player_unit.hy) < 4:
					continue
				
				unit.hx, unit.hy = hx, hy
				scenario.map_hexes[(hx, hy)].unit_stack.append(unit)
				break
		
		# set up VP hexes and generate initial VP console
		scenario.CenterVPOnPlayer()
		scenario.SetVPHexes()
		
		# set up map objectives for this scenario
		for i in range(3):
			for tries in range(300):
				(hx, hy) = choice(scenario.map_hexes.keys())
				# already an objective
				if scenario.map_hexes[(hx, hy)].objective is not None:
					continue
				if scenario.map_hexes[(hx, hy)].terrain_type == 'pond':
					continue
				if GetHexDistance(hx, hy, scenario.player_unit.hx, scenario.player_unit.hy) < 5:
					continue
				
				# too close to an existing objective
				too_close = False
				for map_hex in scenario.map_objectives:
					if GetHexDistance(hx, hy, map_hex.hx, map_hex.hy) < 6:
						too_close = True
						break
				if too_close: continue
				
				scenario.SetObjectiveHex(hx, hy, 1)
				break
		
		# set up start of first phase
		scenario.DoStartOfPhase()
		
		SaveGame()
	
	# generate consoles for first time
	UpdateVPCon()
	UpdateUnitCon()
	UpdatePlayerInfoCon()
	UpdateCrewPositionCon()
	UpdateCommandCon()
	UpdateContextCon()
	UpdateUnitInfoCon()
	UpdateObjectiveInfoCon()
	UpdateScenarioDisplay()
	
	# record mouse cursor position to check when it has moved
	mouse_x = -1
	mouse_y = -1
	
	trigger_end_of_phase = False
	exit_scenario = False
	while not exit_scenario:
		libtcod.console_flush()
		
		# emergency loop escape
		if libtcod.console_is_window_closed(): sys.exit()
		
		# scenario end conditions have been met
		if scenario.finished:
			EraseGame()
			# FUTURE: add more descriptive detail here
			text = 'The scenario is over: ' + scenario.win_desc
			ShowNotification(text)
			exit_scenario = True
			continue
		
		# if player is not active, do AI actions
		if scenario.game_turn['active_player'] == 1:
			for unit in scenario.units:
				if not unit.alive: continue
				if unit.owning_player == 1:
					unit.ai.DoPhaseAction()
			
			Wait(5)
			scenario.NextPhase()
			UpdatePlayerInfoCon()
			UpdateContextCon()
			UpdateObjectiveInfoCon()
			UpdateCrewPositionCon()
			UpdateCommandCon()
			UpdateScenarioDisplay()
			continue
		
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,
			key, mouse)
		
		# check to see if mouse cursor has moved
		if mouse.cx != mouse_x or mouse.cy != mouse_y:
			mouse_x = mouse.cx
			mouse_y = mouse.cy
			UpdateHexTerrainCon()
			UpdateUnitInfoCon()
			UpdateScenarioDisplay()
		
		##### Player Keyboard Commands #####
		
		# exit game
		if key.vk == libtcod.KEY_ESCAPE:
			result = ShowGameMenu(None)
			if result == 'exit_game':
				exit_scenario = True
			else:
				# re-draw to clear game menu from screen
				libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
			continue
		
		# automatically trigger next phase for player
		if scenario.game_turn['active_player'] == 0 and scenario.game_turn['current_phase'] == 'Spotting':
			trigger_end_of_phase = True
		
		# next phase
		if trigger_end_of_phase or key.vk == libtcod.KEY_ENTER:
			trigger_end_of_phase = False
			
			# check for automatic next phase and set flag if true
			# I know this is a little awkward but it only seems to work this way
			result = scenario.NextPhase()
			if result:
				trigger_end_of_phase = True
			
			if scenario.finished:
				continue
			
			UpdatePlayerInfoCon()
			UpdateContextCon()
			UpdateObjectiveInfoCon()
			UpdateCrewPositionCon()
			UpdateCommandCon()
			UpdateScenarioDisplay()
		
		# skip reset of this section if no key commands in buffer
		if key.vk == libtcod.KEY_NONE: continue
		
		# key commands
		key_char = chr(key.c).lower()
		
		if scenario.game_turn['current_phase'] == 'Crew Actions':
			
			# change selected crewman
			if key_char in ['i', 'k']:
				
				if key_char == 'i':
					if scenario.selected_position > 0:
						scenario.selected_position -= 1
					else:
						scenario.selected_position = len(scenario.player_unit.crew_positions) - 1
				
				else:
					if scenario.selected_position == len(scenario.player_unit.crew_positions) - 1:
						scenario.selected_position = 0
					else:
						scenario.selected_position += 1
				UpdateContextCon()
				UpdateCrewPositionCon()
				UpdateScenarioDisplay()
			
			# set action for selected crewman
			elif key_char in ['j', 'l']:
				
				position = scenario.player_unit.crew_positions[scenario.selected_position]
				
				# check for empty position
				if position.crewman is not None:
					if key_char == 'j':
						result = position.crewman.SetAction(False)
					else:
						result = position.crewman.SetAction(True)
					if result:
						UpdateContextCon()
						UpdateCrewPositionCon()
						scenario.player_unit.CalcFoV()
						UpdateVPCon()
						UpdateScenarioDisplay()
			
			# toggle hatch for this position
			elif key_char == 'h':
				
				position = scenario.player_unit.crew_positions[scenario.selected_position]
				if position.crewman is not None:
					if position.ToggleHatch():
						UpdateCrewPositionCon()
						scenario.player_unit.CalcFoV()
						UpdateVPCon()
						UpdateScenarioDisplay()
		
		elif scenario.game_turn['current_phase'] == 'Movement':
		
			# move player unit forward
			if key_char == 'w':
				
				if scenario.player_unit.MoveForward():
					UpdatePlayerInfoCon()
					UpdateContextCon()
					UpdateCrewPositionCon()
					scenario.CenterVPOnPlayer()
					scenario.SetVPHexes()
					UpdateVPCon()
					UpdateUnitCon()
					UpdateObjectiveInfoCon()
					UpdateHexTerrainCon()
					UpdateScenarioDisplay()
					libtcod.console_flush()
					SaveGame()
					
					# check for end of movement
					if scenario.player_unit.move_finished:
						trigger_end_of_phase = True
			
			# pivot hull facing
			elif key_char in ['a', 'd']:
				
				if key_char == 'a':
					result = scenario.player_unit.Pivot(False)
				else:
					result = scenario.player_unit.Pivot(True)
				if result:
					scenario.CenterVPOnPlayer()
					scenario.SetVPHexes()
					UpdateContextCon()
					UpdateVPCon()
					UpdateUnitCon()
					UpdateObjectiveInfoCon()
					UpdateHexTerrainCon()
					UpdateScenarioDisplay()
			
		elif scenario.game_turn['current_phase'] == 'Combat':
			
			# select weapon
			if key_char in ['w', 's']:
				if key_char == 'w':
					result = scenario.SelectNextWeapon(False)
				else:
					result = scenario.SelectNextWeapon(True)
				if result:
					UpdateContextCon()
					UpdateScenarioDisplay()
			
			# rotate turret facing
			elif key_char in ['q', 'e']:
				if key_char == 'q':
					result = scenario.player_unit.RotateTurret(False)
				else:
					result = scenario.player_unit.RotateTurret(True)
				if result:
					UpdateUnitCon()
					UpdateVPCon()
					UpdateScenarioDisplay()
			
			# select target
			elif key_char in ['a', 'd']:
				if key_char == 'a':
					result = scenario.SelectNextTarget(False)
				else:
					result = scenario.SelectNextTarget(True)
				if result:
					UpdateContextCon()
					UpdateUnitCon()
					UpdateScenarioDisplay()
			
			# fire the active weapon at the selected target
			elif key_char == 'f':
				result = scenario.player_unit.Attack(scenario.selected_weapon,
					scenario.player_target, 'point_fire')
				if result:
					# clear player target
					scenario.player_target = None
					UpdatePlayerInfoCon()
					UpdateCrewPositionCon()
					UpdateVPCon()
					UpdateUnitCon()
					UpdateScenarioDisplay()
					SaveGame()
		
		# wait for a short time to avoid repeated keyboard inputs
		Wait(15)



##########################################################################################
#                                      Main Script                                       #
##########################################################################################

print 'Starting ' + NAME + ' version ' + VERSION	# startup message
os.putenv('SDL_VIDEO_CENTERED', '1')			# center game window on screen
fontname = 'c64_16x16.png'				# TEMP - only one font for now

# set up custom font for libtcod
libtcod.console_set_custom_font(DATAPATH+fontname, libtcod.FONT_LAYOUT_ASCII_INROW, 0, 0)

# set up root console
libtcod.console_init_root(WINDOW_WIDTH, WINDOW_HEIGHT, NAME + ' - ' + VERSION,
	fullscreen = False, renderer = libtcod.RENDERER_GLSL)
libtcod.sys_set_fps(LIMIT_FPS)
libtcod.console_set_default_background(0, libtcod.black)
libtcod.console_set_default_foreground(0, libtcod.white)
libtcod.console_clear(0)

# set up double buffer console
con = libtcod.console_new(WINDOW_WIDTH, WINDOW_HEIGHT)
libtcod.console_set_default_background(con, libtcod.black)
libtcod.console_set_default_foreground(con, libtcod.white)
libtcod.console_clear(con)

# darken screen console
darken_con = libtcod.console_new(WINDOW_WIDTH, WINDOW_HEIGHT)
libtcod.console_set_default_background(darken_con, libtcod.black)
libtcod.console_set_default_foreground(darken_con, libtcod.black)
libtcod.console_clear(darken_con)

# game menu console: 84x54
game_menu_bkg = LoadXP('game_menu.xp')
game_menu_con = libtcod.console_new(84, 54)
libtcod.console_set_default_background(game_menu_con, libtcod.black)
libtcod.console_set_default_foreground(game_menu_con, libtcod.white)
libtcod.console_clear(game_menu_con)

# create mouse and key event holders
mouse = libtcod.Mouse()
key = libtcod.Key()

# for a unit in 0,0 facing direction 0, the location of map hexes in each sextant, up to range 6
# used for checking field of view for the player, covered arcs for weapons, etc.
HEXTANTS = []
for direction in range(6):
	hex_list = [
		(0,-1),								# range 1
		(1,-2), (0,-2), (-1,-1),					# range 2
		(1,-3), (0,-3), (-1,-2),					# range 3
		(2,-4), (1,-4), (0,-4), (-1,-3), (-2,-2),			# range 4
		(2,-5), (1,-5), (0,-5), (-1,-4), (-2,-3),			# range 5
		(3,-6), (2,-6), (1,-6), (0,-6), (-1,-5), (-2,-4), (-3,-3)	# range 6
	]
	if direction != 0:
		for i, (hx, hy) in enumerate(hex_list):
			hex_list[i] = RotateHex(hx, hy, direction)
	HEXTANTS.append(hex_list)



##########################################################################################
#                                        Main Menu                                       #
##########################################################################################

# list of unit images to display on main menu
TANK_IMAGES = ['unit_pz_38t_a.xp']

# gradient animated effect for main menu
GRADIENT = [
	libtcod.Color(51, 51, 51), libtcod.Color(64, 64, 64), libtcod.Color(128, 128, 128),
	libtcod.Color(192, 192, 192), libtcod.Color(255, 255, 255), libtcod.Color(192, 192, 192),
	libtcod.Color(128, 128, 128), libtcod.Color(64, 64, 64), libtcod.Color(51, 51, 51),
	libtcod.Color(51, 51, 51)
]

# set up gradient animation timing
time_click = time.time()
gradient_x = WINDOW_WIDTH + 20


# draw the main menu to the main menu console
def UpdateMainMenuCon():
	
	global main_menu_con
	
	# generate main menu console
	main_menu_con = libtcod.console_new(WINDOW_WIDTH, WINDOW_HEIGHT)
	libtcod.console_set_default_background(main_menu_con, libtcod.black)
	libtcod.console_set_default_foreground(main_menu_con, libtcod.white)
	libtcod.console_clear(main_menu_con)
	
	# display game title
	libtcod.console_blit(LoadXP('main_title.xp'), 0, 0, 0, 0, main_menu_con, 0, 0)
	
	# randomly display a tank image to use for this session
	libtcod.console_blit(LoadXP(choice(TANK_IMAGES)), 0, 0, 0, 0, main_menu_con, 7, 6)
	
	# display version number and program info
	libtcod.console_set_default_foreground(main_menu_con, libtcod.red)
	libtcod.console_print_ex(main_menu_con, WINDOW_XM, WINDOW_HEIGHT-8, libtcod.BKGND_NONE,
		libtcod.CENTER, 'Development Build: Has bugs and incomplete features')
	
	libtcod.console_set_default_foreground(main_menu_con, libtcod.light_grey)
	libtcod.console_print_ex(main_menu_con, WINDOW_XM, WINDOW_HEIGHT-6, libtcod.BKGND_NONE,
		libtcod.CENTER, VERSION)
	libtcod.console_print_ex(main_menu_con, WINDOW_XM, WINDOW_HEIGHT-4,
		libtcod.BKGND_NONE, libtcod.CENTER, 'Copyright 2018')
	libtcod.console_print_ex(main_menu_con, WINDOW_XM, WINDOW_HEIGHT-3,
		libtcod.BKGND_NONE, libtcod.CENTER, 'Free Software under the GNU GPL')
	libtcod.console_print_ex(main_menu_con, WINDOW_XM, WINDOW_HEIGHT-2,
		libtcod.BKGND_NONE, libtcod.CENTER, 'www.armouredcommander.com')
	
	# display menu options
	OPTIONS = [('C', 'Continue'), ('N', 'New Game'), ('Q', 'Quit')]
	y = 38
	for (char, text) in OPTIONS:
		# grey-out continue game option if no saved game present
		disabled = False
		if char == 'C' and not os.path.exists('savegame'):
			disabled = True
		
		if disabled:
			libtcod.console_set_default_foreground(main_menu_con, libtcod.dark_grey)
		else:
			libtcod.console_set_default_foreground(main_menu_con, libtcod.light_blue)
		libtcod.console_print(main_menu_con, WINDOW_XM-5, y, char)
		
		if disabled:
			libtcod.console_set_default_foreground(main_menu_con, libtcod.dark_grey)
		else:
			libtcod.console_set_default_foreground(main_menu_con, libtcod.lighter_grey)
		libtcod.console_print(main_menu_con, WINDOW_XM-3, y, text)	
		
		y += 1


# update the animation effect
def AnimateMainMenu():
	
	global gradient_x
	
	for x in range(0, 10):
		if x + gradient_x > WINDOW_WIDTH: continue
		for y in range(19, 34):
			char = libtcod.console_get_char(main_menu_con, x + gradient_x, y)
			fg = libtcod.console_get_char_foreground(main_menu_con, x + gradient_x, y)
			if char != 0 and fg != GRADIENT[x]:
				libtcod.console_set_char_foreground(main_menu_con, x + gradient_x,
					y, GRADIENT[x])
	gradient_x -= 2
	if gradient_x <= 0: gradient_x = WINDOW_WIDTH + 20


# generate and display the main menu console for the first time
UpdateMainMenuCon()
libtcod.console_blit(main_menu_con, 0, 0, 0, 0, 0, 0, 0)

# Main Menu loop
exit_game = False

while not exit_game:
	
	# trigger animation and update screen
	if time.time() - time_click >= 0.05:
		AnimateMainMenu()
		libtcod.console_blit(main_menu_con, 0, 0, 0, 0, 0, 0, 0)
		time_click = time.time()
	
	libtcod.console_flush()
	libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
	
	# exit right away
	if libtcod.console_is_window_closed(): sys.exit()
	
	if key is None: continue
	
	key_char = chr(key.c).lower()
	
	if key_char == 'q':
		exit_game = True
		continue
	
	if key_char == 'c':
		if not os.path.exists('savegame'):
			continue
		DoScenario(load_game=True)
		UpdateMainMenuCon()
		libtcod.console_blit(main_menu_con, 0, 0, 0, 0, 0, 0, 0)
		libtcod.console_flush()
		Wait(15)
	
	if key_char == 'n':
		# check for overwrite of existing saved game
		if os.path.exists('savegame'):
			text = 'Starting a new scenario will overwrite the existing saved game.'
			result = ShowNotification(text, confirm=True)
			if not result:
				libtcod.console_blit(main_menu_con, 0, 0, 0, 0, 0, 0, 0)
				Wait(15)
				continue
		
		DoScenario()
		UpdateMainMenuCon()
		libtcod.console_blit(main_menu_con, 0, 0, 0, 0, 0, 0, 0)
		libtcod.console_flush()
		Wait(15)

# END #

