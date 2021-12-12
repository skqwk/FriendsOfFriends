import requests, json, time, os, pathlib
from network_graph import Node
from network_graph import Link

MAX_BATCH_SIZE = 25
PRIVATE_PROFILE = False
PAUSE_BETWEEN_REQUESTS = 0.2

requestToGetFriends = "https://api.vk.com/method/friends.get?user_id"
requestToGetDataOfUser = "https://api.vk.com/method/users.get?user_ids"
getMultiple = "https://api.vk.com/method/execute?code=return ["
fieldsForFriends = "&fields=name,sex,city,bdate,education"
with open("token.txt", encoding='utf8') as file:
    TOKEN_AND_VERSION = file.readline()

# Интерфейс для main.py
def getGraphData(mainId, mode):
    if mode == "on":
        mainData = getMainData(mainId) 
        linkData = getLinksByMainId(mainId) 

        mainNode = Node(mainId, mainData) 
        linkNodes = createNodesFromLinks(linkData) 

        nodes = []
        nodes.append(mainNode) 
        nodes.extend(linkNodes) 

        links = []
        links.extend(createLinksBetween(mainId, mainNode, linkNodes))
        links.extend(getMutualLinksBetween(mainId, mainNode, linkNodes))

        graph = {"nodes": [], "links": []}
        deleteSameNodes(nodes)
        addNodesToGraph(graph, nodes)
        addLinksToGraph(graph, links)

        dumpJson(graph, mainNode)
    if mode == "off":
        mainData = getMainData(mainId)
        mainNode = Node(mainId, mainData) 
        graph = loadJson(mainNode)
    if mode == "load":
        mainData = getMainData(mainId)
        mainNode = Node(mainId, mainData) 

        additionalData = "&fields=sex,bdate,education,city"
        loadingData = {}
        loadingData = getResponseFromVKBy(requestToGetDataOfUser, additionalData, mainId)
        with open(f'graphs/{mainNode.name}.txt', 'w') as fp:
            json.dump(loadingData, fp)

    return graph

# Локальная реализация
def getMainData(mainId):
    additionalData = "&fields=sex,bdate,education,city"
    data = getResponseFromVKBy(requestToGetDataOfUser, additionalData, mainId)
    # print(data)
    userData = data[0]
    mainData = getProcessedData(userData)
    return mainData

def getLinksByMainId(mainId):
    data = getResponseFromVKBy(requestToGetFriends, fieldsForFriends, mainId)
    amountFriends = data["count"] 
    friends = data["items"] 
    return friends

def getProcessedData(userData):
    mainData = {}
    additionalData = {}
    processedData = [mainData, additionalData]
    
    mainData["name"] = userData["first_name"] + " " + userData["last_name"]
    mainData["sex"] = "female" if (userData["sex"] == 1) else "male"
    try:
        additionalData["bdate"] = userData["bdate"]
    except KeyError:
        additionalData["bdate"] = ""
    try:
        additionalData["city"] = userData["city"]["title"]
    except KeyError:
        additionalData["city"] = ""
    try:
        additionalData["education"] = userData["university_name"]
    except KeyError:
        additionalData["education"] = ""
    return processedData
def createNodesFromLinks(friends):
    nodes = []
    for friend in friends:
        data = getProcessedData(friend)
        node = Node(friend["id"], data)
        nodes.append(node)
    return nodes

def createLinksBetween(mainId, sourceNode, targetNodes):
    links = []
    for targetNode in targetNodes:
        linksNotCreated = (sourceNode.id < targetNode.id) 
        if (linksNotCreated or sourceNode.id == mainId):
            link = Link(sourceNode.name, targetNode.name)
            links.append(link)
    return links

def getMutualLinksBetween(mainId, mainNode, nodesOfFriends):
    batches = []
    batches = splitOnBatches(nodesOfFriends) 
    links = []
    node_MutualID = {}
    for batchOfNodes in batches:
        time.sleep(PAUSE_BETWEEN_REQUESTS)
        node_MutualID = (getMutualFriends(mainNode, batchOfNodes))
        for node in batchOfNodes:
            if node_MutualID[node] != PRIVATE_PROFILE:
                targetNodes = getNodesByID(nodesOfFriends, node_MutualID[node])
                mutualLinks = createLinksBetween(mainId, node, targetNodes)
                links.extend(mutualLinks) 
    return links

def splitOnBatches(nodes):
    counterOfNodes = 1
    i = 0
    batchOfNodes = []
    batches = []
    for node in nodes:
        # print(node.id, " ", counterOfNodes)
        if i < MAX_BATCH_SIZE:
            batchOfNodes.append(node)
            i+=1
        else:
            batches.append(batchOfNodes)
            batchOfNodes = []
            batchOfNodes.append(node)
            i = 1
        counterOfNodes+=1
    batches.append(batchOfNodes)
    return batches

def getMutualFriends(mainNode, batchOfNodes):
    url = createMultipleQueryToGetMutual(mainNode, batchOfNodes)
    response = requests.get(url)
    mutualFriends = exctractResponse(response)

    node_MutualID = dict(zip(batchOfNodes, mutualFriends))
    return node_MutualID

def createMultipleQueryToGetMutual(mainNode, batchOfNodes):
    url = getMultiple
    i = 0
    source = mainNode.id
    for node in batchOfNodes:
        target = node.id
        endOfTheBatch = len(batchOfNodes)-1
        if i != endOfTheBatch:
            url += f"API.friends.getMutual({{source_uid:{source}, target_uid:{target}}}),"
        else:
            url += f"API.friends.getMutual({{source_uid:{source}, target_uid:{target}}})];"
        i += 1
    url+=TOKEN_AND_VERSION
    return url

def getNodesByID(nodes, ids): 
    neccesaryNodes = []
    for id in ids:
        for node in nodes:
            if id == node.id:
                neccesaryNodes.append(node)
    return neccesaryNodes

def getResponseFromVKBy(nameOfRequest, fields, mainId):
    url = f"{nameOfRequest}={mainId}&lang=en{fields}{TOKEN_AND_VERSION}"
    response = requests.get(url) 
    data = exctractResponse(response)
    return data

def exctractResponse(response):
    try:
        data = response.json()["response"]
    except KeyError:
        # придумать обработку исключений TODO
        error = response.json()["error"]
        print(error["error_msg"])
        return 0
    return data


def deleteSameNodes(nodes):
    name = {}
    for node in nodes:
        name[node.name] = 0
    for node in nodes:
        name[node.name] += 1
    for node in nodes:
        if name[node.name] > 1:
            # print(node.name)
            nodes.remove(node)
            name[node.name] -= 1


def addNodesToGraph(graph, nodes):
    for node in nodes:
        nodeJSON = {"id" : node.name, "sex": node.sex, "hashCode": node.id}
        nodeJSON.update(node.additionalData)
        graph["nodes"].append(nodeJSON)

def addLinksToGraph(graph, links):
    for link in links:
        linkJSON = {"source" : link.source, "target" : link.target}
        graph["links"].append(linkJSON)

def dumpJson(graph, mainNode):
    filePath = f'graphs/{mainNode.name}.json'
    path = pathlib.Path(os.getcwd()).joinpath(filePath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(filePath, 'w') as fp:
        json.dump(graph, fp)

def loadJson(mainNode):
    with open(f'graphs/{mainNode.name}.json') as data:
        graph = json.load(data)
        return graph