import dash_core_components as dcc
import dash_html_components as html
import networkx as nx
import plotly.graph_objects as go
import dash



# классы в отдельный файл, чтобы не было четкой связи между визуализатором и источником данных TODO
class Node:
   def __init__(self, id, data):
      self.name = data[0]["name"]
      self.sex = data[0]["sex"]
      self.additionalData = data[1]
      self.id = id

class Link:
   def __init__(self, source, target):
      self.source = source
      self.target = target

def visualizeGraph(data, argument):
    G = nx.readwrite.json_graph.node_link_graph(data)
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    for n, p in pos.items():
        G.nodes[n]['pos'] = p


    # создаем словарь позиций по каждому узлу
    # устанавливаем позицию для каждого узла

    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        # проходимся по ребрам графа, ребро состоит из двух узлов, 
        # поэтому получаем по очереди координаты первого узла, а потом второго
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)
        # добавляем координаты каждого ребра в массив в формате: 
        # edge_x = [x0, x1, None, x0, x1, None, ...]
        # т.е. разрывая начало и конец через None

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        name = "сетка",
        mode='lines')

    fig = go.Figure(data=edge_trace,
                layout=go.Layout(
                    showlegend=True,
                    width = 1400,
                    height = 800,
                    title=f'<br>Social graph of {data["nodes"][0]["id"]}',))

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = G.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)
    if len(G.nodes()) != len(data["nodes"]):
        print(f"G.nodes = {len(G.nodes())}    data[nodes] = "+str(len(data["nodes"])))
    # сделать exception с несовпадением len(G.nodes()) и len(data["nodes"]) TODO
    # argument = "city"
    filters = splitByArgument(argument, data)

    node_text = []
    node_link = []
    for node in data["nodes"]:
        name = node["id"]
        hashCode = node["hashCode"]
        city = node["city"]
        education = node["education"]
        stroke = f"Name: <b>{name}</b> <br></br> id: <b>{hashCode}</b> <br></br> city: <b>{city}</b> <br></br> education: <b>{education}</b>"
        node_text.append(stroke)
        node_link.append("vk.com/id"+str(node["hashCode"]))
       
        
    batchOfNums = []
    for filter in filters:
        i = 0
        nums = []
        for node in data["nodes"]:
            if node[argument] == filter:
                nums.append(i)
            i+=1
        batchOfNums.append(nums)


    filter_x = []
    filter_y = []
    batchOfTxt = []
    for nums in batchOfNums:
        newNode_x = []
        newNode_y = []
        text = []
        for num in nums:
            text.append(node_text[num])
            newNode_x.append(node_x[num])
            newNode_y.append(node_y[num])
        batchOfTxt.append(text)
        filter_x.append(newNode_x)
        filter_y.append(newNode_y)

    i = 0

    

    for filter in filters:
        fig.add_trace(go.Scatter(
            x = filter_x[i],
            y = filter_y[i],
            legendgroup=f"group{i}", 
            name=filter,
            hoverinfo = "text",
            text = batchOfTxt[i],
            mode="markers",
            marker=dict(
                color=i+1, #colors[ran.randint(0, len(colors)-1)] - генератор случайных цветов - запасной вариант
                size=20, 
                line_width=2)

        ))
        i+=1
    
    fig.update_layout(
    font=dict(size=18)
)

    app = dash.Dash(__name__)
    app.layout = html.Div([dcc.Graph(figure=fig)])
    app.run_server(debug=False)
    

def splitByArgument(argument, data):
    filters = set()
    for node in data["nodes"]:
        filters.add(node[argument])
    return filters
    