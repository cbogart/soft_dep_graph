import networkx as nx
from networkx.algorithms.centrality import eigenvector_centrality
import matplotlib.pyplot as plt
import community

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
        
    def from_mongo_tables(self, linkrecords, app_info):
        """Build graph from mongo table contents
        
        @param linkrecords: list of dicts with keys: focal, other, type, raw_count, scaled_count
        @param app_info: dictionary of app title -> application entry from mongo
        """
        for link in linkrecords:
            self.G.add_node(link["focal"])
            self.G.add_node(link["other"])
            self.G.add_edge(link["focal"], link["other"], weight=link["raw_count"])
        
        self.names = {}
        names = { app_info[app]["_id"]: app_info[app]["title"] for app in app_info }
        for n in self.G.nodes():
            #if n not in names: 
            self.names[n] = names[n] if n in names else "unknown"
        
    def draw_graph(self, output_file=None):
        """Draw a graph of used-with connections between packages
        
        @param output_file: file to save graph to; if None, then show graph
        """
        partition = community.best_partition(self.G)
        pos=nx.spring_layout(self.G,iterations=2)  
        plt.clf()
    
        plt.title('usedwith')
        nx.draw(self.G,pos,node_size=15,labels=self.names, with_edges=False, 
                with_labels=False, node_color=[hashColor(partition[n]) for n in self.G.nodes()])
        if output_file is None:
            plt.show()
        else:
            plt.savefig(output_file)
        
        
    def calc_centrality(self):
        """Calculate eigenvector centrality measure for each package or application"""
        return eigenvector_centrality(self.G)
 