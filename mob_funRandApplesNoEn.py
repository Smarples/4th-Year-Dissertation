# ------------------------------------------------------------------------------------------------
# Copyright (c) 2016 Microsoft Corporation
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ------------------------------------------------------------------------------------------------

import MalmoPython
import logging
import os
import random
import sys
import time
import json
import random
import errno
import math
import Tkinter as tk
from collections import namedtuple
EntityInfo = namedtuple('EntityInfo', 'x, y, z, name, colour, variation, quantity')
EntityInfo.__new__.__defaults__ = (0, 0, 0, "", "", "", 1)

# Task parameters:
NUM_GOALS = 20
GOAL_TYPE = "apple"
GOAL_REWARD = 200
PAIN_REWARD = -50
WALL_REWARD = -5
FINISH_REWARD = 1000
ARENA_WIDTH = 20
ARENA_BREADTH = 20
MOB_SPAWNER_PERCENTAGE = 0.1
MOB_TYPE = "Zombie"  # Change for fun, but note that spawning conditions have to be correct - eg spiders will require darker conditions.

# Display parameters:
CANVAS_BORDER = 20
CANVAS_WIDTH = 400
CANVAS_HEIGHT = CANVAS_BORDER + ((CANVAS_WIDTH - CANVAS_BORDER) * ARENA_BREADTH / ARENA_WIDTH)
CANVAS_SCALEX = (CANVAS_WIDTH-CANVAS_BORDER)/ARENA_WIDTH
CANVAS_SCALEY = (CANVAS_HEIGHT-CANVAS_BORDER)/ARENA_BREADTH
CANVAS_ORGX = -ARENA_WIDTH/CANVAS_SCALEX
CANVAS_ORGY = -ARENA_BREADTH/CANVAS_SCALEY

# Agent parameters:
agent_stepsize = 1
agent_search_resolution = 10 # Smaller values make computation faster, which seems to offset any benefit from the higher resolution.
agent_goal_weight = 100
agent_edge_weight = -100
agent_mob_weight = -10
agent_turn_weight = 0 # Negative values to penalise turning, positive to encourage.

#randomly generates mob spawners along the edge, dependant on spawn percentage
def getSpawnerXML():
    ''' Build an XML string that contains some randomly positioned goal items'''
    xml=""
    for x in range(-ARENA_WIDTH/2,ARENA_WIDTH/2):
        if random.random()<MOB_SPAWNER_PERCENTAGE:
             xml += '''<DrawBlock x ="''' + str(x) + '''" y = "206" z = " ''' + str(ARENA_WIDTH/2) + ''' " type = "mob_spawner" variant ="''' + MOB_TYPE + '''"/>''' 
        if random.random()<MOB_SPAWNER_PERCENTAGE:
             xml += '''<DrawBlock x ="''' + str(x) + '''" y = "206" z = " ''' + str(-ARENA_WIDTH/2) + ''' " type = "mob_spawner" variant ="''' + MOB_TYPE + '''"/>''' 
    for z in range(-ARENA_BREADTH/2,ARENA_BREADTH/2):
        if random.random()<MOB_SPAWNER_PERCENTAGE:
             xml += '''<DrawBlock x =" ''' + str(-ARENA_BREADTH/2) + ''' " y = "206" z = " ''' + str(z) + ''' " type = "mob_spawner" variant ="''' + MOB_TYPE + '''"/>''' 
        if random.random()<MOB_SPAWNER_PERCENTAGE:
             xml += '''<DrawBlock x =" ''' + str(ARENA_BREADTH/2) + '''" y = "206" z = " ''' + str(z) + ''' " type = "mob_spawner" variant ="''' + MOB_TYPE + '''"/>''' 
    return xml

#randomly generates apples in created space
def getItemXML():
    ''' Build an XML string that contains some randomly positioned goal items'''
    xml=""
    for item in range(NUM_GOALS):
        x = str(random.randint(-ARENA_WIDTH/2,ARENA_WIDTH/2))
        z = str(random.randint(-ARENA_BREADTH/2,ARENA_BREADTH/2))
        xml += '''<DrawItem x="''' + x + '''" y="210" z="''' + z + '''" type="''' + GOAL_TYPE + '''"/>'''
    return xml

#returns the coordinates of the top corners
def getCorner(index,top,left,expand=0,y=206):
    ''' Return part of the XML string that defines the requested corner'''
    x = str(-(expand+ARENA_WIDTH/2)) if left else str(expand+ARENA_WIDTH/2)
    z = str(-(expand+ARENA_BREADTH/2)) if top else str(expand+ARENA_BREADTH/2)
    return 'x'+index+'="'+x+'" y'+index+'="' +str(y)+'" z'+index+'="'+z+'"'

#<DrawLine ''' + getCorner("1",True,True) + " " + getCorner("2",True,False) + spawn_end_tag + '''
#                    <DrawLine ''' + getCorner("1",True,True) + " " + getCorner("2",False,True) + spawn_end_tag + '''
#                    <DrawLine ''' + getCorner("1",False,False) + " " + getCorner("2",True,False) + spawn_end_tag + '''
#                    <DrawLine ''' + getCorner("1",False,False) + " " + getCorner("2",False,True) + spawn_end_tag + '''
#draw random apples
#                    


def getMissionXML(summary):
    ''' Build an XML mission string.'''
    spawn_end_tag = ' type="mob_spawner" variant="' + MOB_TYPE + '"/>'
    return '''<?xml version="1.0" encoding="UTF-8" ?>
    <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <About>
            <Summary>''' + summary + '''</Summary>
        </About>

        <ModSettings>
            <MsPerTick>20</MsPerTick>
        </ModSettings>
        <ServerSection>
            <ServerInitialConditions>
                <Time>
                    <StartTime>14000</StartTime>
                    <AllowPassageOfTime>false</AllowPassageOfTime>
                </Time>
                <AllowSpawning>false</AllowSpawning>
            </ServerInitialConditions>
            <ServerHandlers>
                <FlatWorldGenerator generatorString="3;7,220*1,5*3,2;3;,biome_1" />
                <DrawingDecorator>
                    <DrawCuboid ''' + getCorner("1",True,True,expand=1) + " " + getCorner("2",False,False,y=226,expand=1) + ''' type="stone"/>
                    <DrawCuboid ''' + getCorner("1",True,True,y=207) + " " + getCorner("2",False,False,y=226) + ''' type="air"/>

                    ''' + getItemXML() + '''

                </DrawingDecorator>
                <ServerQuitFromTimeUp timeLimitMs="60000" description="timeup"/>
                <ServerQuitWhenAnyAgentFinishes />
            </ServerHandlers>
        </ServerSection>

        <AgentSection mode="Survival">
            <Name>The Hunted</Name>
            <AgentStart>
                <Placement x="5" y="207.01" z="5"/>
                <Inventory>
                </Inventory>
            </AgentStart>
            <AgentHandlers>
                <ChatCommands/>
                <ContinuousMovementCommands turnSpeedDegs="360"/>
                <AbsoluteMovementCommands/>
                <ObservationFromNearbyEntities>
                    <Range name="full" xrange="'''+str(ARENA_WIDTH)+'''" yrange="5" zrange="'''+str(ARENA_BREADTH)+'''" />
                    <Range name="entities" xrange="2" yrange="2" zrange="2" />
                </ObservationFromNearbyEntities>
                <ObservationFromFullStats/>
                



                <RewardForMissionEnd rewardForDeath="-1000">
                    <Reward description="timeup" reward="0" />
                </RewardForMissionEnd>
                <RewardForSendingCommand reward="-1" />




                <RewardForCollectingItem>
                    <Item type="'''+GOAL_TYPE+'''" reward="'''+str(GOAL_REWARD)+'''"/>
                </RewardForCollectingItem>
            </AgentHandlers>
        </AgentSection>

    </Mission>'''

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------
class TabQAgent:
    """Tabular Q-learning agent for discrete state/action spaces."""

    def __init__(self):
        self.epsilon = 0.01 # chance of taking a random action instead of the best
        self.disfact = 0.95 # discount factor for future actions
        self.alpha = 0.1

        self.logger = logging.getLogger(__name__)
        if False: # True if you want to see more information
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        self.logger.handlers = []
        self.logger.addHandler(logging.StreamHandler(sys.stdout))

        self.actions = ["turn -0.8", "turn -0.6", "turn -0.4", "turn -0.2", "turn 0", "turn 0.2", "turn 0.4", "turn 0.6", "turn 0.8", "turn 1" ]
        self.q_table = {}
        self.best_q_table = {}
        self.bestScore = None
        self.bestSteps = None
        self.finishtimes = []
        self.appleCount = []
        self.apples = 20
        self.commands = []
        #locations of apples
        self.locations = {}
        #number of visits to particular location
        self.visits = {}
        #self.next is the best action in next state
        self.next = None
        self.canvas = None
        self.root = None

    def updateQTable( self, reward, current_state ):
        """Change q_table to reflect what we have learnt."""
        
        # retrieve the old action value from the Q-table (indexed by the previous state and the previous action)
        old_q = self.q_table[self.prev_s][self.prev_a]
        
        # TODO: what should the new action value be?
        new_q = reward
        
        # assign the new action value to the Q-table
        self.q_table[self.prev_s][self.prev_a] = new_q
        
    def updateQTableFromTerminatingState( self, reward ):
        """Change q_table to reflect what we have learnt, after reaching a terminal state."""
        
        # retrieve the old action value from the Q-table (indexed by the previous state and the previous action)
        old_q = self.q_table[self.prev_s][self.prev_a]
        
        # TODO: what should the new action value be?
        new_q = reward
        
        # assign the new action value to the Q-table
        self.q_table[self.prev_s][self.prev_a] = new_q

    def visit(self,current_s, a):

        if not self.visits.has_key((current_s,a)):
            self.visits[(current_s,a)] = (1)
        else:
            self.visits[(current_s,a)] += 1

        alpha = 1/float(1 + (self.visits[(current_s,a)]))
        return alpha
        
    def act(self, world_state, agent_host, current_r ):
        """take 1 action in response to the current world state"""
        
        step_reward = -1

        obs_text = world_state.observations[-1].text
        obs = json.loads(obs_text) # most recent observation
        self.logger.debug(obs)
        if not u'XPos' in obs or not u'ZPos' in obs:
            self.logger.error("Incomplete observation received: %s" % obs_text)
            return 0
        current_s = "%d:%d" % (int(obs[u'XPos']), int(obs[u'ZPos']))
        self.logger.debug("State: %s (x = %.2f, z = %.2f)" % (current_s, float(obs[u'XPos']), float(obs[u'ZPos'])))
        if not self.q_table.has_key(current_s):
            self.q_table[current_s] = ([0] * len(self.actions))

        # update Q values

        if "Yaw" in obs:
            current_yaw = obs[u'Yaw']

        #change for selecting action-----------------------------------------------------------------------------------------------------------------------------------------
        #code for non initial actions
        if self.prev_s is not None:
          
            #finds best action in next state
            m = max(self.q_table[current_s])
            l = list()
            for x in range(0, len(self.actions)):
                #add every option that rewards the same as the best to a list
                if self.q_table[current_s][x] == m:
                    l.append(x)
            y = random.randint(0, len(l)-1)
            q = l[y]

            i = -0.8
            count = 0
            while (i <= 1):
                if (q == count):
                    q_angle = i
                count += 1
                i += 0.2
            #now have q_table angle

            #change action into degrees, find the difference between agent current direction, change back into previous form
            q_angle *= 180.0
            difference = q_angle - current_yaw;
            while difference < -180:
                difference += 360;
            while difference > 180:
                difference -= 360;
            difference /= 180.0;
            
            #a is the amount the agent has to turn to change to the required angle
            a_angle = difference
            i = -0.8
            count = 0
            while (i <= 1):
                if (a_angle >= (i-0.1) and a_angle <= (i + 0.1)):
                    a = count
                if (a_angle >= -1.1) and a_angle <= (-0.9):
                    a = 9
                count += 1
                i += 0.2
            
            if self.locations.has_key((current_s)):
                if (self.apples == 1):
                    step_reward += FINISH_REWARD
                self.locations.pop(current_s, None)
                step_reward += GOAL_REWARD

            if str(ARENA_WIDTH/2) in str(current_s) or str(-((ARENA_WIDTH/2)-1)) in str(current_s):
                step_reward+=WALL_REWARD
                current_r += WALL_REWARD

            #best
            old_q = self.q_table[self.prev_s][self.prev_a]
            #self.q_table[self.prev_s][self.prev_a] =  old_q + self.alpha * (step_reward + self.disfact * max(self.q_table[current_s]) - old_q)

            #straight line & improved but not curvy
            self.q_table[self.prev_s][self.prev_a] = (1-self.visit(self.prev_s,self.prev_a)) * old_q + self.visit(self.prev_s,self.prev_a) * (step_reward + self.disfact * max(self.q_table[current_s]))

        #code for the initial action 
        else:
            if "entities" in obs:
                #stores the x,y,z,name,colour,variation,quantity for each entity
                entities = [EntityInfo(**k) for k in obs["entities"]]
            #finds best angle
            best_yaw = getBestAngle(entities, current_yaw, current_life)

            #difference is best angle - agents current facing angle
            difference = best_yaw - current_yaw;
            while best_yaw < -180:
                best_yaw += 360;
            while best_yaw > 180:
                best_yaw -= 360;
            best_yaw /= 180.0;
            #q-action = action angle for use in the q table
            q_action = best_yaw

            while difference < -180:
                difference += 360;
            while difference > 180:
                difference -= 360;
            difference /= 180.0;
            #a_action is agent action for agent to turn a certain amount using self.actions
            a_action = difference
            
            #changes the difference angle into an action
            i = -0.8
            count = 0
            while (i <= 1):
                if (q_action >= (i-0.1) and q_action <= (i + 0.1)):
                    q = count
                if (a_action >= (i-0.1) and a_action <= (i + 0.1)):
                    a = count
                count += 1
                i += 0.2

        # try to send the selected action, only update prev_s if this succeeds
        try:
            agent_host.sendCommand(self.actions[a])
            self.prev_s = current_s
            self.prev_a = q

        except RuntimeError as e:
            self.logger.error("Failed to send command: %s" % e)

        return current_r

    def run(self, agent_host):
        """run the agent on the world"""

        self.prev_s = None
        self.prev_a = None
        self.visits = {}


        current_yaw = 0
        best_yaw = 0
        current_life = 0 
        total_reward = 0
        total_commands = 0
        flash = False
        start = time.time()
        apples = None
        #world state contains observations, rewards and frames since last state
        world_state = agent_host.getWorldState()
        # main loop:
        while world_state.is_mission_running:
            world_state = agent_host.getWorldState()
            count = NUM_GOALS
            current_r = 0
            if world_state.number_of_observations_since_last_state > 0:
                count = 0
                msg = world_state.observations[-1].text
                ob = json.loads(msg)
                #current s stores x and z coordinates as whole numbers 
                current_s = "%d:%d" % (int(ob[u'XPos']), int(ob[u'ZPos']))
                #finds current direction player is facing
                if "Yaw" in ob:
                    current_yaw = ob[u'Yaw']
                #sets life as variable, prints message when hit and reward decreases


                if "Life" in ob:
                    life = ob[u'Life']
                    if life < current_life:
                        current_r += PAIN_REWARD
                        agent_host.sendCommand("chat aaaaaaaaargh!!!")
                        flash = True
                    current_life = life
                if "entities" in ob:
                #stores the x,y,z,name,colour,variation,quantity for each entity
                    entities = [EntityInfo(**k) for k in ob["entities"]]
                if "full" in ob:
                    #stores the x,y,z,name,colour,variation,quantity for each entity
                    full = [EntityInfo(**k) for k in ob["full"]]
                    for e in full:
                        if (e.name == "apple"):
                            location = "%d:%d" % (int(e.x), (int(e.z) ))
                            self.locations[(location)] = 1
                            count += 1
                            applec = NUM_GOALS - count
                    self.apples = count
                    if count == 0 and apples is None:
                        end = time.time()
                        finish = end - start
                        if (finish < 2.0):
                            apples = None
                        else:
                            self.finishtimes += [finish]
                            self.commands += [total_commands]
                            applec = 20
                            self.appleCount += [applec]
                            apples = "GOOD"
                            total_reward+=FINISH_REWARD
                            temp_reward = total_reward
                            temp_steps = total_commands
                            temp_q_table = self.q_table
                            if (total_reward > self.bestScore):
                                self.bestScore = total_reward
                                self.bestSteps = total_commands
                                self.best_q_table = self.q_table

                    drawMobs(full, flash)
                #run act to apply action to agent
                if world_state.is_mission_running and len(world_state.observations)>0 and not world_state.observations[-1].text=="{}":
                    total_reward += self.act(world_state, agent_host, current_r)
                    total_commands += 1
            if world_state.number_of_rewards_since_last_state > 0:
                count = NUM_GOALS
                for reward in world_state.rewards:
                    total_reward += reward.getValue()
                #total_reward += world_state.rewards[-1].getValue()
            #end the game when the apples are collected, spawn block that ends game?, have time limit? find a way to break out of main loop without breaking game------------------
            time.sleep(0.02)
            flash = False

        # mission has ended.
        for error in world_state.errors:
            print "Error:",error.text
        if world_state.number_of_rewards_since_last_state > 0:
            for reward in world_state.rewards:
                current_r += reward.getValue()
            #total_reward += world_state.rewards[-1].getValue()

        total_reward += current_r
        #count = 20 means all apples collected
        #stores and displays the appropraite information about the run
        if apples is None:
            end = time.time()
            finish = end - start
            self.finishtimes += [finish]
            self.commands += [total_commands]
            self.appleCount += [applec]
            if (total_reward > self.bestScore):
                self.bestScore = total_reward
                self.bestSteps = total_commands
                self.best_q_table = self.q_table
        else:
            total_reward = temp_reward 
            total_commands = temp_steps
            self.q_table = temp_q_table 

        print "We stayed alive for " + str(total_commands) + " commands, and scored " + str(total_reward)

        #update from terminating state

        return total_reward
        
    
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#NEED TO ADD MORE DETAILS TO RECORDING DIRECTORY-----------------------------------------------------------------------------------
recordingsDirectory="ReinforcementLearningMob"
try:
    os.makedirs(recordingsDirectory)
except OSError as exception:
    if exception.errno != errno.EEXIST: # ignore error if already existed
        raise

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately

#title of popup window
root = tk.Tk()
root.wm_title("Collect the " + GOAL_TYPE + "s, dodge the " + MOB_TYPE + "s!")
#sets the diameters of the popup map
canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, borderwidth=0, highlightthickness=0, bg="black")
canvas.pack()
root.update()

#finds the position of enemies and apples
def findUs(entities):
    for ent in entities:
        if ent.name == MOB_TYPE:
            continue
        elif ent.name == GOAL_TYPE:
            continue
        else:
            return ent

#looks around and uses the details to find the best direction to go, one without enemies or with apples
def getBestAngle(entities, current_yaw, current_health):
    '''Scan through 360 degrees, looking for the best direction in which to take the next step.'''
    us = findUs(entities)
    scores=[]
    # Normalise current yaw:
    while current_yaw < 0:
        current_yaw += 360
    while current_yaw > 360:
        current_yaw -= 360

    # Look for best option
    for i in xrange(agent_search_resolution):
        # Calculate cost of turning:
        #ang increases by ~0.2 for each 12 degrees 
        ang = 2 * math.pi * (i / float(agent_search_resolution))
        #yaw is every angle in 12 degrees 360/ resolution(currently 30)
        yaw = i * 360.0 / float(agent_search_resolution)
        yawdist = min(abs(yaw-current_yaw), 360-abs(yaw-current_yaw))
        turncost = agent_turn_weight * yawdist
        score = turncost

        # Calculate entity proximity cost for new (x,z):
        x = us.x + agent_stepsize - math.sin(ang)
        z = us.z + agent_stepsize * math.cos(ang)
        for ent in entities:
            dist = (ent.x - x)*(ent.x - x) + (ent.z - z)*(ent.z - z)
            #used to stop errors when ent is the player
            if (dist == 0):
                continue
            weight = 0.0
            if ent.name == MOB_TYPE:
                weight = agent_mob_weight
                dist -= 1   # assume mobs are moving towards us
                if dist <= 0:
                    dist = 0.1
            elif ent.name == GOAL_TYPE:
                weight = agent_goal_weight * current_health / 20.0
            score += weight / float(dist)

        # Calculate cost of proximity to edges:
        distRight = (2+ARENA_WIDTH/2) - x
        distLeft = (-2-ARENA_WIDTH/2) - x
        distTop = (2+ARENA_BREADTH/2) - z
        distBottom = (-2-ARENA_BREADTH/2) - z
        score += agent_edge_weight / float(distRight * distRight * distRight * distRight)
        score += agent_edge_weight / float(distLeft * distLeft * distLeft * distLeft)
        score += agent_edge_weight / float(distTop * distTop * distTop * distTop)
        score += agent_edge_weight / float(distBottom * distBottom * distBottom * distBottom)
        scores.append(score)

    # Find best score:
    i = scores.index(max(scores))
    # Return as an angle in degrees:
    return i * 360.0 / float(agent_search_resolution)

#sets size of pop up map
def canvasX(x):
    return (CANVAS_BORDER/2) + (0.5 + x/float(ARENA_WIDTH)) * (CANVAS_WIDTH-CANVAS_BORDER)

def canvasY(y):
    return (CANVAS_BORDER/2) + (0.5 + y/float(ARENA_BREADTH)) * (CANVAS_HEIGHT-CANVAS_BORDER)

#creates mobs
def drawMobs(entities, flash):
    canvas.delete("all")
    if flash:
        canvas.create_rectangle(0,0,CANVAS_WIDTH,CANVAS_HEIGHT,fill="#ff0000") # Pain.
    canvas.create_rectangle(canvasX(-ARENA_WIDTH/2), canvasY(-ARENA_BREADTH/2), canvasX((ARENA_WIDTH/2)), canvasY((ARENA_BREADTH/2)), fill="#888888")
    for ent in entities:
        if ent.name == MOB_TYPE:
            canvas.create_oval(canvasX(ent.x)-2, canvasY(ent.z)-2, canvasX(ent.x)+2, canvasY(ent.z)+2, fill="#ff2244")
        elif ent.name == GOAL_TYPE:
            canvas.create_oval(canvasX(ent.x)-3, canvasY(ent.z)-3, canvasX(ent.x)+3, canvasY(ent.z)+3, fill="#4422ff")
        else:
            canvas.create_oval(canvasX(ent.x)-4, canvasY(ent.z)-4, canvasX(ent.x)+4, canvasY(ent.z)+4, fill="#22ff44")
    root.update()

validate = True
# Create a pool of Minecraft Mod clients.
# By default, mods will choose consecutive mission control ports, starting at 10000,
# so running four mods locally should produce the following pool by default (assuming nothing else
# is using these ports):
my_client_pool = MalmoPython.ClientPool()
my_client_pool.add(MalmoPython.ClientInfo("127.0.0.1", 10000))
my_client_pool.add(MalmoPython.ClientInfo("127.0.0.1", 10001))
my_client_pool.add(MalmoPython.ClientInfo("127.0.0.1", 10002))
my_client_pool.add(MalmoPython.ClientInfo("127.0.0.1", 10003))

agent = TabQAgent()
agent_host = MalmoPython.AgentHost()
try:
    agent_host.parse( sys.argv )
except RuntimeError as e:
    print 'ERROR:',e
    print agent_host.getUsage()
    exit(1)
if agent_host.receivedArgument("help"):
    print agent_host.getUsage()
    exit(0)

if agent_host.receivedArgument("test"):
    num_reps = 1
else:
    num_reps = 20

current_yaw = 0
best_yaw = 0
current_life = 0

cumulative_rewards = []
for iRepeat in range(num_reps):
    mission_xml = getMissionXML(MOB_TYPE + " Apocalypse #" + str(iRepeat))
    my_mission = MalmoPython.MissionSpec(mission_xml,validate)

    max_retries = 3
    for retry in range(max_retries):
        try:
            # Set up a recording
            my_mission_record = MalmoPython.MissionRecordSpec(recordingsDirectory + "//" + "Mission_" + str(iRepeat) + ".tgz")
            my_mission_record.recordRewards()
            my_mission_record.recordCommands()

            # Attempt to start the mission:
            agent_host.startMission( my_mission, my_client_pool, my_mission_record, 0, "predatorExperiment" )
            break
        except RuntimeError as e:
            if retry == max_retries - 1:
                print "Error starting mission",e
                print "Is the game running?"
                exit(1)
            else:
                time.sleep(0.1)

    world_state = agent_host.getWorldState()
    while not world_state.has_mission_begun:
        time.sleep(0.1)
        world_state = agent_host.getWorldState()

    agent_host.sendCommand("move 1")    # run!
    #-------
    cumulative_reward = agent.run(agent_host)
    print 'Cumulative reward: %d' % cumulative_reward
    print 'Number of runs %d' % iRepeat
    cumulative_rewards += [ cumulative_reward ]

    filename = "Mob_funRandApplesNoEnResults.txt"
    file = open(filename, 'w')
    file.write("Rewards \n %s \n Completion times \n  %s \n Number of commands \n  %s \n  Number of Apples Collected \n %s \n Best Score \n  %s \n Best commands \n  %s \n Best Q Table \n  %s \n Last Q Table \n %s \n" %
               (cumulative_rewards, agent.finishtimes,  agent.commands, agent.appleCount, agent.bestScore, agent.bestSteps, agent.best_q_table, agent.q_table))
    # -- clean up -- #
    time.sleep(0.5) # (let the Mod reset)