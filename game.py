import random, string, time, os
import numpy as np
import grid
import time
import analyse
import nameFilter

np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning) 
games = {}
#maxGameLength = 55 + (10 * gridSize) + (90 * (howManyEachAction * clientCount))

### I may have stole this from https://stackoverflow.com/a/25588771 and edited it quite a bit. -used to make printing pretty of course! ###

class prettyPrinter():
    def flattenList(self, t):
        flat_list = [item for sublist in t for item in sublist]
        return flat_list

    def format__1(self, digits,num):
        if digits<len(str(num)):
            raise Exception("digits<len(str(num))")
        return ' '*(digits-len(str(num))) + str(num)
    def printmat(self, arr,row_labels, col_labels): #print a 2d numpy array (maybe) or nested list
        max_chars = max([len(str(item)) for item in self.flattenList(arr)+col_labels]) #the maximum number of chars required to display any item in list
        if row_labels==[] and col_labels==[]:
            for row in arr:
                print('[%s]' %(' '.join(self.format__1(max_chars,i) for i in row)))
        elif row_labels!=[] and col_labels!=[]:
            rw = max([len(str(item)) for item in row_labels]) #max char width of row__labels
            print('%s %s' % (' '*(rw+1), ' '.join(self.format__1(max_chars,i) for i in col_labels)))
            for row_label, row in zip(row_labels, arr):
                print('%s [%s]' % (self.format__1(rw,row_label), ' '.join(self.format__1(max_chars,i) for i in row)))
        else:
            raise Exception("This case is not implemented...either both row_labels and col_labels must be given, or neither.")


#   ___       .    __   __ .____           .    __    _ .___          ___  .     _ .____  __    _  _______        ___   ____    _______ .____    ___   _______   _____
# .'   \     /|    |    |  /              /|    |\   |  /   `       .'   \ /     | /      |\   |  '   /         .'   `. /   \  '   /    /      .'   \ '   /     (     
# |         /  \   |\  /|  |__.          /  \   | \  |  |    |      |      |     | |__.   | \  |      |         |     | |,_-<      |    |__.   |          |      `--. 
# |    _   /---'\  | \/ |  |            /---'\  |  \ |  |    |      |      |     | |      |  \ |      |         |     | |    `     |    |      |          |         | 
#  `.___|,'      \ /    /  /----/     ,'      \ |   \|  /---/        `.__, /---/ / /----/ |   \|      /          `.__.' `----'  `--/    /----/  `.__,     /    \___.' 
### CLASSES USED TO DESCRIBE GAMES AND CLIENTS ###
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------

def updateBOARDS(gameName, whatToUpdate):
    BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
    if whatToUpdate[0] == None:
        BOARDS[gameName][1] = whatToUpdate[1]
    elif whatToUpdate[1] == None:
        BOARDS[gameName][0] = whatToUpdate[0]
    else:
        BOARDS[gameName] = whatToUpdate
    np.save("boards.npy", BOARDS)

class gameHandler():
    def __init__(self, about, overwriteAbout):
        maxEstTime = about["turnTime"] * about["gridDim"][0] * about["gridDim"][1]
        self.about = {"name":about["gameName"], "status":"lobby", "playerCap":about["playerCap"], "nameUniqueFilter":about["nameUniqueFilter"], "nameNaughtyFilter":about["nameNaughtyFilter"], "turnTime":about["turnTime"], "maxEstTime":maxEstTime, "admins":about["admins"], "gridDim":about["gridDim"], "turnNum":-1, "tileOverride":False, "chosenTiles":{}, "clients":{}, "gridTemplate":grid.grid(about["gridDim"])}
        self.about["eventHandler"] = analyse.gameEventHandler(self)
        self.tempGroupChoices = {}
        self.randomCoords = []

        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        if overwriteAbout == None:
            updateBOARDS(self.about["name"], [self.about, {}])
            print(self.about["name"], "@@@@ CREATED by clients", str(self.about["admins"]), "with properties...", self.about)
        else:
            self.about = overwriteAbout
            updateBOARDS(self.about["name"], [self.about, None])
            print(self.about["name"], "@@@@ RECOVERED with properties...", self.about, "and boards", BOARDS[about["gameName"]][1])
        
        self.pP = prettyPrinter()
    
    def writeAboutToBoards(self):
        updateBOARDS(self.about["name"], [self.about, None])
    
    def whoIsOnThatLine(self, choice):
        coord = choice
        if type(choice) == int:
            rOrC = 1
        else:
            rOrC = 0
        victims = []
        for client in self.about["clients"]:
            if rOrC == "column":
                if self.about["clients"][client].about["column"] == coord:
                    victims.append(client)
            else:
                if self.about["clients"][client].about["row"] == coord:
                    victims.append(client)
        return victims
    
    def groupDecisionAdd(self, clientName, event, choice):
        if event["event"] == "D":
                self.tempGroupChoices[clientName] = choice
        self.writeAboutToBoards()

    def groupDecisionConclude(self, event):
        if event["event"] == "D":
            whoMirrored = []
            whoShielded = []
            for key, value in self.tempGroupChoices.items():
                if value == "mirror":
                    whoMirrored.append(key)
                elif value == "shield":
                    whoShielded.append(key)
            
            if len(whoMirrored) > 1: #Mirror
                rOrC = event["other"][0]
                if rOrC == 1:
                    choice = event["sources"][0].about["column"]
                else:
                    choice = event["sources"][0].about["row"]
                victims = self.game.whoIsOnThatLine(rOrC, choice)
                self.about["events"].append(self.game.about["eventHandler"].make({"public":True, "event":event["event"], "sources":whoMirrored, "targets":[self.game.about["clients"][victim] for victim in victims], "isMirrored":True, "isShielded":False, "other":[rOrC, choice]})) #EVENT HANDLER
                for victim in victims:
                    self.game.about["clients"][victim].beActedOn("D", self.about) ###ACT
            
            elif len(whoShielded) > 1: #Shield
                self.about["events"].append(self.game.about["eventHandler"].make({"public":True, "event":event["event"], "sources":whoShielded, "targets":[], "isMirrored":False, "isShielded":True, "other":[]})) #EVENT HANDLER
            
            else:
                for clientName in self.tempGroupChoices:
                    self.about["clients"][clientName].forceActedOn("D")
            self.tempGroupChoices = []
        self.writeAboutToBoards()

    def turnProcess(self):
        actions = []
        clientsShuffled = list(self.about["clients"].keys())
        random.shuffle(clientsShuffled)
        didTheirTurn = {}
        for clientName in clientsShuffled:
            didTheirTurn[clientName] = False
        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        for clientName, value in didTheirTurn.items():
            if not value:
                x = self.about["chosenTiles"][self.about["turnNum"]][0]
                y = self.about["chosenTiles"][self.about["turnNum"]][1]
                self.about["clients"][clientName].about["tileHistory"].append(BOARDS[self.about["name"]][1][clientName][x][y])
                if self.about["clients"][clientName].act(BOARDS[self.about["name"]][1][clientName][x][y]) != None:
                    didTheirTurn[clientName] = True

        if False not in didTheirTurn.values():
            self.about["turnNum"] += 1
            for clientName in clientsShuffled:
                self.about["clients"][clientName].logScore()
        self.writeAboutToBoards()
            
    def info(self):
        return {"about":self.about, "gridTemplate":self.about["gridTemplate"].about}
    
    def status(self): #= lobby, active, awaiting, dormant
        return self.about["status"]

    def leaderboard(self):
        clientByScore = {}
        for client in self.about["clients"]:
            clientByScore[client] = self.about["clients"][client].about["scoreHistory"][-1]
        out = {}
        for client in sorted(clientByScore, key=clientByScore.get, reverse=True):
            out[client] = {"score":clientByScore[client], "money":self.about["clients"][client].about["money"], "bank":self.about["clients"][client].about["bank"]}
        return out
    
    def joinLobby(self, clients):
        out = []
        for i in range(len(clients)):
            if clients[i]["name"] == "":
                clients[i]["name"] = ''.join(random.choice(string.ascii_letters) for x in range(6))
            nameCheck = nameFilter.checkString(self.about["clients"].keys(), clients[i]["name"], nameNaughtyFilter = 0.85, nameUniqueFilter = 0.85)
            if nameCheck == None: #(no problems with the name)
                if len(self.about["clients"].items()) < self.about["playerCap"]:
                    if self.about["status"] == "lobby":
                        try:
                            self.about["clients"][clients[i]["name"]] = clientHandler(self, clients[i]["name"], clients[i])
                            self.about["clients"][clients[i]["name"]].buildRandomBoard()
                            self.writeAboutToBoards()
                            out.append(True)
                            print(self.about["name"], "@@@@", clients[i]["name"], "has joined the lobby.")
                        except Exception as e:
                            out.append(e)
                    else:
                        out.append("The game is not in the lobby stage, it is in: " + self.about["status"])
                else:
                    out.append("The player cap of " + str(self.about["playerCap"]) + " has been reached.")
            else:
                print(clients[i]["name"])
                out.append("The username " + clients[i]["name"] + " doesn't pass the name filters: " + str(nameCheck))
        return out
    
    def leave(self, clients):
        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        out = []
        for clientName in clients:
            try:
                del self.about["clients"][clientName]
                del BOARDS[self.about["name"]][1][clientName]
                self.writeAboutToBoards()
                out.append(True)
                print(self.about["name"], "@@@@", clientName, "has left the lobby.")
            except:
                out.append(False)
        BOARDS = np.save("boards.npy", BOARDS)
        return out

    def printBoards(self):
        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        for client in self.about["clients"]:
            print(self.about["name"], "@ Client", self.about["clients"][client].about["name"], "has info", self.about["clients"][client].about, "and board...")
            row_labels = [str(y+1) for y in range(self.about["gridDim"][1])]
            col_labels = [str(x+1) for x in range(self.about["gridDim"][0])]
            tempBOARD = BOARDS[self.about["name"]][1][client]
            for tile in self.about["chosenTiles"]:
                tempBOARD[tile[1]][tile[0]] = "-"
            self.pP.printmat(tempBOARD, row_labels, col_labels)
    
    def serialReadBoard(self, clientName, positions):
        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        return self.about["gridTemplate"].serialReadBoard(BOARDS[self.about["name"]][1][clientName], positions)
    
    def serialWriteBoard(self, gameName, clientName, serial):
        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        BOARDS[self.about["name"]][1][clientName] = self.about["gridTemplate"].serialWriteBoard(BOARDS[self.about["name"]][1][clientName], serial)
        BOARDS = np.save("boards.npy", BOARDS)

    def start(self):
        self.about["status"] = "paused"
        self.about["turnNum"] += 1

        self.randomCoords = []
        for x in range(self.about["gridDim"][0]):
            for y in range(self.about["gridDim"][1]):
                self.randomCoords.append((x,y))
        random.shuffle(self.randomCoords)
        print(self.about["name"], "@@@ STARTED with", len(self.about["clients"]), "clients, here's more info...", self.info())
        self.printBoards()
        self.writeAboutToBoards()
        return True
    
    def filterClients(self, gameName, requirements, clients=[]):
        if clients == []:
            clients = self.about["clients"]
        out = []
        for clientName,about in clients.items():
            wrongTally = 0
            for key,value in requirements.items():
                if clients[clientName].about[key] != value:
                    wrongTally += 1
            if wrongTally == 0:
                out[clientName] = about
        return out

    def turnHandle(self):
        if self.about["turnNum"] < 0:
            raise Exception("The game is on turn -1, which can't be handled.")
        if self.about["turnNum"] < self.about["gridDim"][0] * self.about["gridDim"][1]:
            if self.about["turnNum"] not in self.about["chosenTiles"].keys():
                if self.about["tileOverride"] == False:
                    notUnique = True
                    while notUnique:
                        newTile = (self.randomCoords[self.about["turnNum"]-1][0], self.randomCoords[self.about["turnNum"]-1][1]) #x,y
                        if newTile not in self.about["chosenTiles"]:
                            notUnique = False
                else:
                    newTile = self.about["tileOverride"]
                    self.about["tileOverride"] = False
                self.about["chosenTiles"][self.about["turnNum"]] = newTile
                print(self.about["name"], "@@ ------------------------ Turn", self.about["turnNum"] + 1, "--- Tile", (newTile[0] + 1, newTile[1] + 1), "------------------------")
            self.turnProcess()
            #self.printBoards()
        else:
            self.about["status"] = "dormant" #this is for when the game doesn't end immediatedly after the turn count is up
            print(gameName, "@@@ Game over.")
            print("Leaderboard:", leaderboard(gameName))
            self.delete()
            deleteGame([self.about["name"]])
        self.writeAboutToBoards()

    
    def delete(self):
        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        del BOARDS[self.about["name"]]
        np.save("boards.npy", BOARDS)

class clientHandler():
    def __init__(self, game, clientName, about):
        self.game = game

        ##TYPE = AI, spectator, human
        if about["type"] == "human":
            self.about = {"name":clientName, "type": about["type"], "ready":False, "events":[], "authCode":''.join(random.choice(string.ascii_letters + string.digits) for x in range(60)), "money":0, "bank":0, "scoreHistory":[], "tileHistory":[], "shield":False, "mirror":False, "row":random.choice(["A", "B", "C"]), "column":str(random.randint(0,2))}
        elif about["type"] == "AI":
            self.about = {"name":clientName, "type": about["type"], "ready":True, "events":[], "authCode":''.join(random.choice(string.ascii_letters + string.digits) for x in range(60)), "money":0, "bank":0, "scoreHistory":[], "tileHistory":[], "shield":False, "mirror":False, "row":random.choice(["A", "B", "C"]), "column":str(random.randint(0,2))}
        elif about["type"] == "spectator":
            self.about = {"name":clientName, "type": about["type"], "ready":True, "authCode":''.join(random.choice(string.ascii_letters + string.digits) for x in range(60))}
        self.about["estimateHandler"] = analyse.clientEstimateHandler(self)
        self.about["FRONTresponses"] = []
        self.about["FRONTquestions"] = []

    def buildRandomBoard(self):
        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        gr = self.game.about["gridTemplate"].build()
        BOARDS[self.game.about["name"]][1][self.about["name"]] = gr
        BOARDS = np.save("boards.npy", BOARDS)
    
    def info(self):
        return {"about":self.about}
    
    def logScore(self):
        self.about["scoreHistory"].append(self.about["money"] + self.about["bank"])
    
    def FRONTresponse(self, choice):
        self.about["FRONTresponses"].append(choice)
    
    def deQueueResponses(self):
        whatIsDeleted = self.about["FRONTresponses"][-1]
        del self.about["FRONTresponses"][-1]
        return whatIsDeleted
    
    def makeQuestionToFRONT(self, question):
        print("A question has been raised.", question)
        self.about["FRONTquestions"].append(question)
        self.game.about["status"] = "awaiting"

    def rOrCChoice(self):
        if self.about["type"] == "AI":
            rOrC = random.choice("row", "column")#randint(0,1)
            if rOrC == "column":
                columns = [str(i) for i in range(3)]
                columns.remove(self.about["column"])
                choice = random.choice(columns)
            else:
                rows = ["A", "B", "C"]
                del rows[self.about["row"] - 1]
                choice = random.choice(rows)
            return choice
        elif self.about["type"] == "human":
            if len(self.about["FRONTquestions"]) == 0:
                self.makeQuestionToFRONT({"gameName":self.game.about["name"], "clientName": self.about["name"], "options":[["A","B","C",0,1,2]], "labels":["which team / ship do you want to attack?"]})
                return None
            elif len(self.about["FRONTresponses"]) > 0:
                return self.deQueueResponses()

    def responseChoice(self):
        options = []
        for key,value in {"none":True, "mirror":self.about["mirror"], "shield":self.about["shield"]}.items():
            if value:
                options.append(key)
        if self.about["type"] == "AI":
            return random.choice(options)
        elif self.about["type"] == "human":
            if len(self.about["FRONTquestions"]) == 0:
                self.makeQuestionToFRONT({"gameName":self.game.about["name"], "clientName": self.about["name"], "options":options, "labels":["How do you want to respond?"]})
                return None
            elif len(self.about["FRONTresponses"]) > 0:
                return self.deQueueResponses()
    
    def victimChoice(self):
        options = []
        for client in self.game.about["clients"]:
            if client != self.about["name"]:
                options.append(client)
        if self.about["type"] == "AI":
            return random.choice(options)
        elif self.about["type"] == "human":
            if len(self.about["FRONTquestions"]) == 0:
                self.makeQuestionToFRONT({"gameName":self.game.about["name"], "clientName": self.about["name"], "options":[options], "labels":["Who do you want to be your victim?"]})
                return None
            elif len(self.about["FRONTresponses"]) > 0:
                return self.deQueueResponses()
    
    def tileChoice(self):
        options = []
        for x in range(self.about["gridDim"][0]):
            for y in range(self.about["gridDim"][1]):
                if (x,y) not in self.about["chosenTiles"]:
                    options.append((x,y))
        return random.choice(options)
        #if self.about["type"] == "AI":
        if True:
            return random.choice(options)
        elif self.about["type"] == "human":
            if len(self.about["FRONTquestions"]) == 0:
                self.makeQuestionToFRONT({"gameName":self.game.about["name"], "clientName": self.about["name"], "options":[options], "labels":["Which tile would you like for the next turn?"]})
                return None
            elif len(self.about["FRONTresponses"]) > 0:
                return self.deQueueResponses()

    def act(self, whatHappened): 
        if whatHappened == "A": #A - Rob
            choice = self.victimChoice()
            if choice != None:
                self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "sources":[self], "targets":[self.game.about["clients"][choice]], "isMirrored":False, "isShielded":False, "other":[]}) #EVENT HANDLER
                self.game.about["clients"][choice].beActedOn("A", self) ###ACT
                #print(self.game.about["name"], "@", self.about["name"], "robs", self.game.about["clients"][choice].about["name"])
            return choice
        if whatHappened == "B": #B - Kill
            choice = self.victimChoice()
            if choice != None:
                self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "sources":[self], "targets":[self.game.about["clients"][choice]], "isMirrored":False, "isShielded":False, "other":[]}) #EVENT HANDLER
                self.game.about["clients"][choice].beActedOn("B", self) ###ACT
                #print(self.game.about["name"], "@", self.about["name"], "kills", self.game.about["clients"][choice].about["name"])
            return choice
        if whatHappened == "C": #C - Present (Give someone 1000 of YOUR OWN cash)
            choice = self.victimChoice()
            if choice != None:
                self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "sources":[self], "targets":[self.game.about["clients"][choice]], "isMirrored":False, "isShielded":False, "other":[]}) #EVENT HANDLER
                self.game.about["clients"][choice].beActedOn("C", self) ###ACT
                #print(self.game.about["name"], "@", self.about["name"], "gifts", self.game.about["clients"][choice].about["name"])
            return choice
        if whatHappened == "D": #D - Skull and Crossbones (Wipe out (Number of players)/3 people)
            choice = self.rOrCChoice()
            if choice != None:
                victims = self.game.whoIsOnThatLine(choice)
                self.about["events"].append(self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "sources":[self], "targets":[self.game.about["clients"][victim] for victim in victims], "isMirrored":False, "isShielded":False, "other":[choice]})) #EVENT HANDLER
                for victim in victims:
                    self.game.about["clients"][victim].beActedOn("D", self) ###ACT
                #if rOrC == "column":
                    #print(self.game.about["name"], "@", self.about["name"], "wiped out column", choice, "which held", [self.game.about["clients"][victim].about["name"] for victim in victims])
                #else:
                    #print(self.game.about["name"], "@", self.about["name"], "wiped out row", choice, "which held", [self.game.about["clients"][victim].about["name"] for victim in victims])
            return choice
        if whatHappened == "E": #E - Swap
            choice = self.victimChoice()
            if choice != None:
                self.about["events"].append(self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "sources":[self], "targets":[self.game.about["clients"][choice]], "isMirrored":False, "isShielded":False, "other":[]})) #EVENT HANDLER
                self.game.about["clients"][choice].beActedOn("E", self) ###ACT
                #print(self.game.about["name"], "@", self.about["name"], "swaps with", self.game.about["clients"][choice].about["name"])
            return choice
        if whatHappened == "F": #F - Choose Next Square
            choice = self.tileChoice()
            if choice != None:
                self.game.about["tileOverride"] = choice
                self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "sources":[self], "targets":[self.game], "isMirrored":False, "isShielded":False, "other":[self.game.about["tileOverride"]]}) #EVENT HANDLER
                #print(self.game.about["name"], "@", self.about["name"], "chose the next square", (self.game.about["tileOverride"][0] + 1, self.game.about["tileOverride"][1] + 1))
            return choice
        if whatHappened == "G": #G - Shield
            self.game.about["eventHandler"].make({"public":False, "event":whatHappened, "sources":[self.game], "targets":[self], "isMirrored":False, "isShielded":False, "other":[]}) #EVENT HANDLER
            self.about["shield"] = True ###ACT
            #print(self.game.about["name"], "@", self.about["name"], "gains a shield.")
            return True
        if whatHappened == "H": #H - Mirror
            self.game.about["eventHandler"].make({"public":False, "event":whatHappened, "sources":[self.game], "targets":[self], "isMirrored":False, "isShielded":False, "other":[]}) #EVENT HANDLER
            self.about["mirror"] = True ###ACT
            #print(self.game.about["name"], "@", self.about["name"], "gains a mirror.")
            return True
        if whatHappened == "I": #I - Bomb (You go to 0)
            self.game.about["eventHandler"].make({"public":False, "event":whatHappened, "sources":[self.game], "targets":[self], "isMirrored":False, "isShielded":False, "other":[]}) #EVENT HANDLER
            self.about["money"] = 0 ###ACT
            #print(self.game.about["name"], "@", self.about["name"], "got bombed.")
            return True
        if whatHappened == "J": #J - Double Cash
            self.game.about["eventHandler"].make({"public":False, "event":whatHappened, "sources":[self.game], "targets":[self], "isMirrored":False, "isShielded":False, "other":[]}) #EVENT HANDLER
            self.about["money"] *= 2 ###ACT
            #print(self.game.about["name"], "@", self.about["name"], "got their cash doubled.")
            return True
        if whatHappened == "K": #K - Bank
            self.game.about["eventHandler"].make({"public":False, "event":whatHappened, "sources":[self.game], "targets":[self], "isMirrored":False, "isShielded":False, "other":[]}) #EVENT HANDLER
            self.about["bank"] += self.about["money"] ###ACT
            self.about["money"] = 0 ###ACT
            #print(self.game.about["name"], "@", self.about["name"], "banked their money.")
            return True
        if whatHappened == "5000": #£5000
            self.game.about["eventHandler"].make({"public":False, "event":whatHappened, "sources":[self.game], "targets":[self], "isMirrored":False, "isShielded":False, "other":[]}) #EVENT HANDLER
            self.about["money"] += 5000 ###ACT
            #print(self.game.about["name"], "@", self.about["name"], "gained £5000.")
            return True
        if whatHappened == "3000": #£3000
            self.game.about["eventHandler"].make({"public":False, "event":whatHappened, "sources":[self.game], "targets":[self], "isMirrored":False, "isShielded":False, "other":[]}) #EVENT HANDLER
            self.about["money"] += 3000 ###ACT
            #print(self.game.about["name"], "@", self.about["name"], "gained £3000.")
            return True
        if whatHappened == "1000": #£1000
            self.game.about["eventHandler"].make({"public":False, "event":whatHappened, "sources":[self.game], "targets":[self], "isMirrored":False, "isShielded":False, "other":[]}) #EVENT HANDLER
            self.about["money"] += 1000 ###ACT
            #print(self.game.about["name"], "@", self.about["name"], "gained £1000.")
            return True
        if whatHappened == "200": #£200
            self.game.about["eventHandler"].make({"public":False, "event":whatHappened, "sources":[self.game], "targets":[self], "isMirrored":False, "isShielded":False, "other":[]}) #EVENT HANDLER
            self.about["money"] += 200 ###ACT
            #print(self.game.about["name"], "@", self.about["name"], "gained £200.")
            return True
    
    def beActedOn(self, whatHappened, sender): #These are all the functions that involve interaction between players
        #if self.about[shield] or self.about[mirror]:
            ###check with the vue server here about whether the user wants to use a shield or mirror?
        if whatHappened == "A":
            choice = self.responseChoice()
            if choice == "none":
                self.game.about["clients"][sender.about["name"]].about["money"] += self.about["money"]
                self.about["money"] = 0
            elif choice == "shield":
                self.about["shield"] = False
                self.about["events"].append(self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "sources":[self], "targets":[], "isMirrored":False, "isShielded":True, "other":[]})) #EVENT HANDLER
            elif choice == "mirror":
                self.about["mirror"] = False
                self.about["events"].append(self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "sources":[self], "targets":[sender], "isMirrored":True, "isShielded":False, "other":[]})) #EVENT HANDLER
                self.game.about["clients"][sender.about["name"]].beActedOn("A", self)

        if whatHappened == "B":
            choice = self.responseChoice()
            if choice == "none":
                self.about["money"], self.about["bank"] = 0, 0
            if choice == "shield":
                self.about["shield"] = False
                self.about["events"].append(self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "sources":[self], "targets":[], "isMirrored":False, "isShielded":True, "other":[]})) #EVENT HANDLER
            elif choice == "mirror":
                self.about["mirror"] = False
                self.about["events"].append(self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "sources":[self], "targets":[sender], "isMirrored":True, "isShielded":False, "other":[]})) #EVENT HANDLER
                self.game.about["clients"][sender.about["name"]].beActedOn("B", self)
        if whatHappened == "C":
            choice = self.responseChoice()
            if choice == "none":
                if self.game.about["clients"][sender.about["name"]].about["money"] >= 1000:
                    self.about["money"] += 1000
                    self.game.about["clients"][sender.about["name"]].about["money"] -= 1000
                elif self.game.about["clients"][sender.about["name"]].about["money"] > 0:
                    self.about["money"] += self.game.about["clients"][sender.about["name"]].about["money"]
                    self.game.about["clients"][sender.about["name"]].about["money"] = 0
            if choice == "shield":
                self.about["shield"] = False
                self.about["events"].append(self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "sources":[self], "targets":[], "isMirrored":False, "isShielded":True, "other":[]})) #EVENT HANDLER
            if choice == "mirror":
                self.about["mirror"] = False
                self.about["events"].append(self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "sources":[self], "targets":[sender], "isMirrored":True, "isShielded":False, "other":[]})) #EVENT HANDLER
                self.game.about["clients"][sender.about["name"]].beActedOn("C", self)
        if whatHappened == "D":
            choice = self.responseChoice()
            self.about["events"].append(self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "sources":[self], "targets":[sender], "isMirrored":True, "isShielded":False, "other":[]})) #EVENT HANDLER
            self.game.groupDecisionAdd(self.about["name"], sender.about["events"][-1], choice)
        if whatHappened == "E":
            self.about["money"], self.game.about["clients"][sender.about["name"]].about["money"] = self.game.about["clients"][sender.about["name"]].about["money"], self.about["money"]
    
    def forceActedOn(self, whatHappened):
        if whatHappened == "D":
            self.about["money"] = 0


# .____ .     . __    _   ___   _______ _   ___   __    _   _____      .____   ___   .___           .    .___  .___ 
# /     /     / |\   |  .'   \ '   /    | .'   `. |\   |   (           /     .'   `. /   \         /|    /   \ /   \
# |__.  |     | | \  |  |          |    | |     | | \  |    `--.       |__.  |     | |__-'        /  \   |,_-' |,_-'
# |     |     | |  \ |  |          |    | |     | |  \ |       |       |     |     | |  \        /---'\  |     |    
# /      `._.'  |   \|   `.__,     /    /  `.__.' |   \|  \___.'       /      `.__.' /   \     ,'      \ /     /    
### FUNCTIONS THAT ALLOW APP.PY TO INTERACT WITH GAME AND CLIENT OBJECTS, ###
### and also the main thread, which includes demo code. ###
# ------------------------------------------------------------------------------------------------------------------

#if not playing will they need an id to see the game stats or is that spoiling the fun?
def listGames():
    return games

def makeGame(about, overwriteAbout = None):
    if about["gameName"] == "":
        about["gameName"] = ''.join(random.choice(string.ascii_letters) for x in range(6))
    print(about["admins"])
    for i in range(len(about["admins"])):
        if about["admins"][i]["name"] == "":
            about["admins"][i]["name"] = ''.join(random.choice(string.ascii_letters) for x in range(6))
    nameCheck = nameFilter.checkString(games.keys(), about["gameName"], nameNaughtyFilter = 0.85, nameUniqueFilter = 0.85)
    if nameCheck == None:
        g = gameHandler(about, overwriteAbout)
        games[about["gameName"]] = g
        out = joinLobby(about["gameName"], about["admins"])
        if all(out):
            return {"gameName":about["gameName"], "admins":about["admins"]}
        else:
            print("error joining clients to the lobby:", out)
            return False
    else:
        print(about["gameName"], "@@@@ FAILED GAME CREATION:", ("The game name " + about["gameName"] + " doesn't pass the name filters: " + str(nameCheck)))
        return False

#delete game(s) by Name
def deleteGame(gameNames):
    success = []
    fail = []
    for gameName in gameNames:
        try:
            games[gameName].delete()
            del games[gameName]
            success.append(gameName)
        except:
            fail.append(gameName)
    if len(fail) > 0:
        print(fail, "@@@@ NOT DELETED", success, "DELETED")
    elif len(success) > 0:
        print(success, "@@@@ DELETED")
    else:
        print("@@@@ NOTHING DELETED")

#get the info of a game by name
def gameInfo(gameName): #gameInfo("testGame")["about"]["admin"]
    try:
        return games[gameName].info()
    except Exception as e:
        return e

#get the info of a client by name and game name
def clientInfo(about): #clientInfo({"gameName":"game1", "clientName":"Jamie"}) returns {"about":about}
    try:
        gameName = about.get("gameName")
        clientName = about.get("clientName")
        return games[gameName].about["clients"][about["clientName"]].info()
    except Exception as e:
        return e

#get the clients of a game by name and return either public or private information
def listClients(gameName, toReturn={"private":False, "human":True, "spectator":True, "AI":True}):
    typesToReturn = []
    for key,value in toReturn.items():
        if value and key != "private":
            typesToReturn.append(key)
    if toReturn["private"]:
        out = {}
        for client in games[gameName].about["clients"]:
            if games[gameName].about["clients"][client].about["type"] in typesToReturn:
                out[client] = games[gameName].about["clients"][client].about
    elif not toReturn["private"]:
        out = {}
        for clientName, obj in games[gameName].about["clients"].items():
            tempAbout = obj.about.copy()
            if tempAbout["type"] in typesToReturn:
                print(obj.about)
                tempAbout["authCode"] = None
                tempAbout["money"] = None
                tempAbout["bank"] = None
                tempAbout["scoreHistory"] = None
                tempAbout["shield"] = None
                tempAbout["mirror"] = None
                tempAbout["column"] = None
                tempAbout["row"] = None
                out[clientName] = tempAbout
                print(obj.about)
    return out

#list the names of all the clients by game name
def listClientNames(gameName):
    out = []
    for client in games[gameName].about["clients"]:
        out.append(games[gameName].about["clients"][client].about["name"])
    return out

#join one or several clients to a lobby
def joinLobby(gameName, clients):
    return games[gameName].joinLobby(clients)

def leave(gameName, clients):
    return games[gameName].leave(clients)

def leaderboard(gameName):
    return games[gameName].leaderboard()

def turnHandle(gameName):
    print("TURN HANDLE WAS CALLED.")
    #playerName = "Alex"
    #print("SORTED EVENTS FOR ALEX", sortEvents(gameName, "timestamp", filterEvents(gameName, {}, ['"' + playerName + '"' + ' in event["sourceNames"] or ' + '"' + playerName + '"' + ' in event["targetNames"]'])))
    return games[gameName].turnHandle()

def start(gameName):
    return games[gameName].start()

def status(gameName):
    return games[gameName].status()

def setStatus(gameName, status):
    games[gameName].about["status"] = status
    return True

def playerCount(gameName):
    return len(games[gameName].about["clients"])

def returnEvents(gameName, about):
    return games[gameName].about["eventHandler"].about["log"]

def readyPerc(gameName):
    return len(games[gameName].filterClients(gameName, {"ready":True}).keys()) / len(games[gameName].about["clients"].keys())

def readyUp(gameName, playerName):
    games[gameName].about["clients"][playerName].about["ready"] = True

def serialReadBoard(gameName, clientName, positions=True):
    return games[gameName].serialReadBoard(clientName, positions)

def serialWriteBoard(gameName, clientName, serial):
    try:
        games[gameName].serialWriteBoard(gameName, clientName, serial)
        #this should work as each player only submits their board once
        return True
    except Exception as e:
        return e

def randomiseBoard(gameName, clientName):
    return games[gameName].about["clients"][clientName].buildRandomBoard()

def FRONTresponse(gameName, clientName, choice):
    games[gameName].about["clients"][clientName].FRONTresponse(choice)
    games[gameName].about["status"] = "active"
    games[gameName].turnHandle()

def filterClients(gameName, requirements, clients=[]):
    return games[gameName].filterClients(gameName, requirements, clients)

def filterEvents(gameName, requirements, parses=[], returnNums=False, events=[]):
    if events == []:
        events = games[gameName].about["eventHandler"].about["log"]
    return games[gameName].about["eventHandler"].filterEvents(events, requirements, parses, returnNums)

def describeEvents(gameName, events):
    return games[gameName].about["eventHandler"].describe(events)

def sortEvents(gameName, key, events=None):
    if events == None:
        return games[gameName].about["eventHandler"].sortEvents(games[gameName].about["eventHandler"].about["log"], key)
    else:
        return games[gameName].about["eventHandler"].sortEvents(events, key)

def shownToClient(gameName, timestamp):
    eventNums = games[gameName].about["eventHandler"].filterEvents(games[gameName].about["eventHandler"].about["log"], {"timestamp":timestamp}, [], True)
    for eventNum in eventNums:
        games[gameName].about["eventHandler"].about["log"][eventNum]["shownToClient"] = True
    if all([games[gameName].about["eventHandler"].about["log"][eventNum]["shownToClient"] for eventNum in range(len(games[gameName].about["eventHandler"].about["log"]))]):
        games[gameName].turnHandle()



#Change the attributes of a client or several by game name
# eg: alterClients("game1", ["Jamie"], {"name":"Gemima"})
#this would change the name of Jamie to Gemima.
#nameUniqueFilter, nameNaughtyFilter, turnTime
def alterClients(gameName, clientNames, alterations):
    success = []
    for clientName in clientNames:
        if clientName in games[gameName].about["clients"]:
            for key,value in alterations.items():
                if key in games[gameName].about["clients"][clientName].about:
                    games[gameName].about["clients"][clientName].about[key] = value
                else:
                    success.append("Key: " + str(key) + " doesn't exist for value " + str(value) + " to be assigned to.")
        else:
            for a in alterations.items():
                success.append("Client" + clientName + "doesn't exist.")

#Change the attributes of a game or several, 
# eg: alterGames(["game1"], {"name":"game2"})
#this would change the name of game1 to game2.
def alterGames(gameNames, alterations):
    success = []
    for gameName in gameNames:
        if gameName in games:
            for key,value in alterations.items():
                if key in games[gameName].about:
                    games[gameName].about[key] = value
                    success.append(True)
                else:
                    success.append("Key", key, "doesn't exist for value", value, "to be assigned to.")
        else:
            for a in alterations.items():
                success.append("Game", gameName, "doesn't exist.")
    return success

def bootstrap(about):
    #Loading games that are "running", stored in boards.npy in case the backend crashes or something.
    def failLoad(exception):
        print("@@@@ No games were loaded because:", exception)
        BOARDS = {}
        np.save("boards.npy", BOARDS)
    try:
        f = open("boards.npy")
        if os.path.getsize("boards.npy") > 0:
            try:
                BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
                if len(BOARDS.keys()) == 0:
                    failLoad("there are no games in boards.npy")
                for gameName in BOARDS:
                    #try:
                    admins = BOARDS[gameName][0]["admins"]
                    gridDim = BOARDS[gameName][0]["gridDim"]
                    turnTime = BOARDS[gameName][0]["turnTime"]
                    playerCap = BOARDS[gameName][0]["playerCap"]
                    nameUniqueFilter = BOARDS[gameName][0]["nameUniqueFilter"]
                    nameNaughtyFilter = BOARDS[gameName][0]["nameNaughtyFilter"]
                    gameAbout = {"gameName":gameName, "admins":admins, "gridDim":gridDim, "turnTime":turnTime, "playerCap":playerCap, "nameUniqueFilter":nameUniqueFilter, "nameNaughtyFilter":nameNaughtyFilter}
                    overwriteAbout = BOARDS[gameName][0]
                    makeGame(gameAbout, overwriteAbout)
                    #turnHandle(gameName)
                    #except Exception as e:
                        #print(gameName, "@@@@ FAILED GAME RECOVERY, it's using a different format:", e)
            except Exception as e:
                failLoad(e)
        else:
            failLoad("file is empty")
    except Exception as e:
        failLoad(e)
    
    #And then deleting all those recovered games, because they're not necessary to test one new game.
    if about["purge"]:
        deleteGame([key for key in games])


# .___   .____  __   __   ___  
# /   `  /      |    |  .'   `.
# |    | |__.   |\  /|  |     |
# |    | |      | \/ |  |     |
# /---/  /----/ /    /   `.__.'
### Used for debugging and testing of the overall structure of how a game should operate in relation to the backend. ###
# -----------------------------

# MAIN THREAD
if __name__ == "__main__":
    bootstrap({"purge":True})
    while True:
        #Let's set up a few variables about our new test game...
        gridDim = (15,15)
        gridSize = gridDim[0] * gridDim[1]
        turnCount = gridSize + 1 #maximum of gridSize + 1
        admins = [{"name":"Jamie", "type":"human"}] #this person is auto added.
        gameName = "Test-Game " + str(time.time())[-6:]
        turnTime = 30
        playerCap = 5
        nameNaughtyFilter = 0
        nameUniqueFilter = 0

        #Setting up a test game
        about = {"gameName":gameName, "admins":admins, "gridDim":gridDim, "turnTime":turnTime, "playerCap":playerCap, "nameUniqueFilter":nameUniqueFilter, "nameNaughtyFilter":nameNaughtyFilter}
        makeGame(about)

        #Adding each of the imaginary players to the lobby sequentially.
        clients = [{"name":"Tom", "type":"human"}, {"name":"Alex", "type":"human"}] #Player name, then info about them which currently consists of whether they're playing.
        print("joining clients to the lobby", joinLobby(gameName, clients)) #This will create all the new players listed above so they're part of the gameHandler instance as individual clientHandler instances.
        #In future, when a user decides they don't want to play but still want to be in a game, the frontend will have to communicate with the backend to tell it to replace the isPlaying attribute in self.game.about["clients"][client].about
        
        clients = [{"name":"Jamie", "type":"human"}] #This is to verify that duplicate usernames aren't allowed.
        print("joining a dupe client to the lobby", joinLobby(gameName, clients))


        #Kicking one of the imaginary players. (regardless of whether the game is in lobby or cycling turns)
        #print("exiting client from the lobby", leave(gameName, ["Jamie"]))

        #Simulating the interaction with the vue server, pinging the processing of each successive turn like the Vue server will every time it's happy with client responses turn-by-turn.
        print("Enter any key to iterate a turn...")
        shallIContinue = input()

        start(gameName)
        while status(gameName) != "awaiting" and gameInfo(gameName)["about"]["turnNum"] < turnCount + 1: #Simulate the frontend calling the new turns over and over.
            #shallIContinue = input()
            if status(gameName) != "awaiting":
                turnHandle(gameName)
                playerName = "Alex"
                print("SORTED EVENTS FOR ALEX", sortEvents(gameName, "timestamp", filterEvents(gameName, {}, ['"' + playerName + '"' + ' in event["sourceNames"] or ' + '"' + playerName + '"' + ' in event["targetNames"]'])))
                print("~", status(gameName), "~")
            #randomiseBoard(gameName, "Tom")
            #print("event log:", returnEvents(gameName, {"public":True}))
            #print("tom's serialised board:", serialReadBoard(gameName, "Tom"))
            #message = [{'x': 0, 'y': 0, 'w': 1, 'h': 1, 'id': 0, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 0, 'y': 1, 'w': 1, 'h': 1, 'id': 8, 'content': 'Rob', 'noResize': True, 'noMove': False}, {'x': 0, 'y': 2, 'w': 1, 'h': 1, 'id': 16, 'content': '1000', 'noResize': True, 'noMove': False}, {'x': 0, 'y': 3, 'w': 1, 'h': 1, 'id': 24, 'content': 'Present', 'noResize': True, 'noMove': False}, {'x': 0, 'y': 4, 'w': 1, 'h': 1, 'id': 32, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 0, 'y': 5, 'w': 1, 'h': 1, 'id': 40, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 0, 'y': 6, 'w': 1, 'h': 1, 'id': 48, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 0, 'y': 7, 'w': 1, 'h': 1, 'id': 56, 'content': 'Bomb', 'noResize': True, 'noMove': False}, {'x': 1, 'y': 0, 'w': 1, 'h': 1, 'id': 1, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 1, 'y': 1, 'w': 1, 'h': 1, 'id': 9, 'content': 'Mirror', 'noResize': True, 'noMove': False}, {'x': 1, 'y': 2, 'w': 1, 'h': 1, 'id': 17, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 1, 'y': 3, 'w': 1, 'h': 1, 'id': 25, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 1, 'y': 4, 'w': 1, 'h': 1, 'id': 33, 'content': 'Kill', 'noResize': True, 'noMove': False}, {'x': 1, 'y': 5, 'w': 1, 'h': 1, 'id': 41, 'content': '3000', 'noResize': True, 'noMove': False}, {'x': 1, 'y': 6, 'w': 1, 'h': 1, 'id': 49, 'content': 'Double', 'noResize': True, 'noMove': False}, {'x': 1, 'y': 7, 'w': 1, 'h': 1, 'id': 57, 'content': 'Shield', 'noResize': True, 'noMove': False}, {'x': 2, 'y': 0, 'w': 1, 'h': 1, 'id': 2, 'content': 'Double', 'noResize': True, 'noMove': False}, {'x': 2, 'y': 1, 'w': 1, 'h': 1, 'id': 10, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 2, 'y': 2, 'w': 1, 'h': 1, 'id': 18, 'content': 'Present', 'noResize': True, 'noMove': False}, {'x': 2, 'y': 3, 'w': 1, 'h': 1, 'id': 26, 'content': '1000', 'noResize': True, 'noMove': False}, {'x': 2, 'y': 4, 'w': 1, 'h': 1, 'id': 34, 'content': '3000', 'noResize': True, 'noMove': False}, {'x': 2, 'y': 5, 'w': 1, 'h': 1, 'id': 42, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 2, 'y': 6, 'w': 1, 'h': 1, 'id': 50, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 2, 'y': 7, 'w': 1, 'h': 1, 'id': 58, 'content': 'Swap', 'noResize': True, 'noMove': False}, {'x': 3, 'y': 0, 'w': 1, 'h': 1, 'id': 3, 'content': '1000', 'noResize': True, 'noMove': False}, {'x': 3, 'y': 1, 'w': 1, 'h': 1, 'id': 11, 'content': 'Shield', 'noResize': True, 'noMove': False}, {'x': 3, 'y': 2, 'w': 1, 'h': 1, 'id': 19, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 3, 'y': 3, 'w': 1, 'h': 1, 'id': 27, 'content': 'Bomb', 'noResize': True, 'noMove': False}, {'x': 3, 'y': 4, 'w': 1, 'h': 1, 'id': 35, 'content': '1000', 'noResize': True, 'noMove': False}, {'x': 3, 'y': 5, 'w': 1, 'h': 1, 'id': 43, 'content': '1000', 'noResize': True, 'noMove': False}, {'x': 3, 'y': 6, 'w': 1, 'h': 1, 'id': 51, 'content': '1000', 'noResize': True, 'noMove': False}, {'x': 3, 'y': 7, 'w': 1, 'h': 1, 'id': 59, 'content': 'Bank', 'noResize': True, 'noMove': False}, {'x': 4, 'y': 0, 'w': 1, 'h': 1, 'id': 4, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 4, 'y': 1, 'w': 1, 'h': 1, 'id': 12, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 4, 'y': 2, 'w': 1, 'h': 1, 'id': 20, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 4, 'y': 3, 'w': 1, 'h': 1, 'id': 28, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 4, 'y': 4, 'w': 1, 'h': 1, 'id': 36, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 4, 'y': 5, 'w': 1, 'h': 1, 'id': 44, 'content': '5000', 'noResize': True, 'noMove': False}, {'x': 4, 'y': 6, 'w': 1, 'h': 1, 'id': 52, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 4, 'y': 7, 'w': 1, 'h': 1, 'id': 60, 'content': 'Choose Next Square', 'noResize': True, 'noMove': False}, {'x': 5, 'y': 0, 'w': 1, 'h': 1, 'id': 5, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 5, 'y': 1, 'w': 1, 'h': 1, 'id': 13, 'content': 'Rob', 'noResize': True, 'noMove': False}, {'x': 5, 'y': 2, 'w': 1, 'h': 1, 'id': 21, 'content': 'Skull and Crossbones', 'noResize': True, 'noMove': False}, {'x': 5, 'y': 3, 'w': 1, 'h': 1, 'id': 29, 'content': '1000', 'noResize': True, 'noMove': False}, {'x': 5, 'y': 4, 'w': 1, 'h': 1, 'id': 37, 'content': 'Skull and Crossbones', 'noResize': True, 'noMove': False}, {'x': 5, 'y': 5, 'w': 1, 'h': 1, 'id': 45, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 5, 'y': 6, 'w': 1, 'h': 1, 'id': 53, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 5, 'y': 7, 'w': 1, 'h': 1, 'id': 61, 'content': '1000', 'noResize': True, 'noMove': False}, {'x': 6, 'y': 0, 'w': 1, 'h': 1, 'id': 6, 'content': '1000', 'noResize': True, 'noMove': False}, {'x': 6, 'y': 1, 'w': 1, 'h': 1, 'id': 14, 'content': 'Choose Next Square', 'noResize': True, 'noMove': False}, {'x': 6, 'y': 2, 'w': 1, 'h': 1, 'id': 22, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 6, 'y': 3, 'w': 1, 'h': 1, 'id': 30, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 6, 'y': 4, 'w': 1, 'h': 1, 'id': 38, 'content': 'Swap', 'noResize': True, 'noMove': False}, {'x': 6, 'y': 5, 'w': 1, 'h': 1, 'id': 46, 'content': 'Mirror', 'noResize': True, 'noMove': False}, {'x': 6, 'y': 6, 'w': 1, 'h': 1, 'id': 54, 'content': '1000', 'noResize': True, 'noMove': False}, {'x': 6, 'y': 7, 'w': 1, 'h': 1, 'id': 62, 'content': '1000', 'noResize': True, 'noMove': False}, {'x': 7, 'y': 0, 'w': 1, 'h': 1, 'id': 7, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 7, 'y': 1, 'w': 1, 'h': 1, 'id': 15, 'content': '1000', 'noResize': True, 'noMove': False}, {'x': 7, 'y': 2, 'w': 1, 'h': 1, 'id': 23, 'content': '1000', 'noResize': True, 'noMove': False}, {'x': 7, 'y': 3, 'w': 1, 'h': 1, 'id': 31, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 7, 'y': 4, 'w': 1, 'h': 1, 'id': 39, 'content': 'Kill', 'noResize': True, 'noMove': False}, {'x': 7, 'y': 5, 'w': 1, 'h': 1, 'id': 47, 'content': '200', 'noResize': True, 'noMove': False}, {'x': 7, 'y': 6, 'w': 1, 'h': 1, 'id': 55, 'content': 'Bank', 'noResize': True, 'noMove': False}, {'x': 7, 'y': 7, 'w': 1, 'h': 1, 'id': 63, 'content': '200', 'noResize': True, 'noMove': False}]
            #print(serialWriteBoard(gameName, "Tom", message))
        
        print("Enter any key to delete the game...")
        shallIContinue = input()

        deleteGame([key for key in games])
        for i in range(3):
            print("")