from soft_dep_graphing import *
from pymongo import MongoClient, Connection
import pickle

c = Connection()
db = c["snm-r"]
lr = db.git_co_occurence_links.find()
app_info = { app["title"]: app  for app in db.application.find() }
gs = db.global_stats.find_one()
git_proj_counts = gs["num_git_projects_scraped"]

try:
    with open('thg.pickle') as f:
        graph = pickle.load(f)
        print "Retrieved graph"
except Exception, e:
    print "Loading graph", (str(e))
    graph = SoftDepGraph()
    graph.from_mongo_tables(lr, app_info, "git_usage", git_proj_counts)
    with open('thg.pickle', 'w') as f:
        pickle.dump(graph, f)

print "Graphing"
#graph.pmi_histogram()
graph.draw_graph("usedwith.png")
