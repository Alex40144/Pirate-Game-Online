from flask import Flask, render_template, request,jsonify
import game
import pymongo

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["mydatabase"]

mycol = mydb["accounts"]

app = Flask(__name__)

@app.route('/api/create_game', methods=['POST'])
def hostGame():
    data = request.get_json()
    gameName = data["gameName"]
    ownerID = data["ownerID"]
    Sizex = data["Sizex"]
    Sizey = data["Sizey"]
    Host = data["isHostPlaying"]

    Dim = (Sizex, Sizey)

    result = game.makeGame(gameName, ownerID, Dim)
    print(result)
    #data = {'game': result[1], 'pass': result[0]}
    data = "Success"
    return jsonify(data)
    #this should tell the client if everything is ok, or custom name already taken.



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")