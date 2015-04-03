import networkx as nx
from networkx.algorithms.centrality import eigenvector_centrality
import matplotlib.pyplot as plt
import community
import math
import numpy

def hashColor(key, selected = False):
    """Return a color unique for this key, brigher if selected.

    Of course the color can't really be unique because there are more keys
    in the world than colors; but the algorithm tries to make similar strings
    come out different colors so they can be distinguished in a chart or graph"""

    def tw(t): return t ^ (t << (t%5)) ^ (t << (6+(t%7))) ^ (t << (13+(t%11)))
    theHash = tw(hash(key) % 5003)
    ifsel = 0x00 if selected else 0x80
    (r,g,b) = (ifsel |  (theHash & 0x7f),
               ifsel | ((theHash>>8) & 0x7F),
               ifsel | ((theHash>>16) & 0x7F))
    return "#{0:02x}{1:02x}{2:02x}".format(r,g,b)

class SoftDepGraph:
    def __init__(self):
        self.G = nx.Graph()
        
    def from_mongo_tables(self, linkrecords, app_info, usage_field, N):
        """Build graph from mongo table contents
        
        @param linkrecords: list of dicts with keys: focal, other, type, raw_count, scaled_count
        @param app_info: dictionary of app title -> application entry from mongo
        """
        self.names = {}
        names = { app_info[app]["_id"]: app_info[app]["title"] for app in app_info }
        for link in linkrecords:
            self.G.add_node(link["focal"])
            self.G.add_node(link["other"])
            px = app_info[names[link["focal"]]][usage_field]*1.0/N
            py = app_info[names[link["other"]]][usage_field]*1.0/N
            pxy = link["raw_count"]*1.0/N 
            npmi = -math.log(pxy/(px*py))/math.log(pxy)
            self.G.add_edge(link["focal"], link["other"], weight=npmi)
            
        for n in self.G.nodes():
            #if n not in names: 
            self.names[n] = names[n] if n in names else "unknown"
        
    def pmi_histogram(self):
        
        wts = [atr["weight"] for (_,_,atr) in self.G.edges_iter(data=True)]
        #import pdb
        #pdb.set_trace()
        
        plt.clf()
        #x = numpy.array(wts)
        h = plt.hist(wts, 50)
        plt.show()

    def draw_graph(self, output_file=None, npmi_threshhold = .7):
        """Draw a graph of used-with connections between packages
        
        @param output_file: file to save graph to; if None, then show graph
        """
        
        G1 = self.G.copy()
        for edge in self.G.edges_iter(data=True):
            if edge[2]["weight"] < npmi_threshhold:
                G1.remove_edge(edge[0], edge[1])
        
        G1 = nx.subgraph(G1, [node for node in G1.nodes() if nx.degree(G1)[node] > 1])        
                
        partition = community.best_partition(G1)
        partpos = nx.spring_layout(community.induced_graph(partition, G1), iterations=100)
        
        forced_partpos = { n : partpos[partition[n]] for n in G1.nodes() }
        print "between"
        pos=nx.spring_layout(G1,pos =forced_partpos,iterations=200)  
        plt.clf()
        plt.figure(figsize=(36,36))
        plt.axis("off")
        
        plt.title('usedwith')

        labels = { node : self.names[node] for node in G1.nodes() }
        nx.draw_networkx_edges(G1,pos, edge_color="#cccccc")
        nx.draw_networkx_nodes(G1,pos,node_size=50, node_color=[hashColor(partition[n]) for n in G1.nodes()])
        nx.draw_networkx_labels(G1,pos,labels=labels)
        if output_file is None:
            plt.show()
        else:
            plt.savefig(output_file, bbox_inches='tight')
        
        
        import pdb
        pdb.set_trace()
        
        
    def calc_centrality(self):
        """Calculate eigenvector centrality measure for each package or application"""
        return eigenvector_centrality(self.G)
 