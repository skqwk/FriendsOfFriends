import time, sys
import requests_to_VK as ds
import network_graph as vs

start = time.time()
graph = ds.getGraphData(mainId = int(sys.argv[1]), mode = sys.argv[2])
end = time.time()
print(f"Runtime of the program is {end - start}")
vs.visualizeGraph(graph, argument=sys.argv[3])
