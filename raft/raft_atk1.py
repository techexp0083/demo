import threading
import time
import random

class Node:
    def __init__(self, node_id, nodes):
        self.node_id = node_id
        self.nodes = nodes
        self.state = 'follower'
        self.term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = 0
        self.last_applied = 0
        self.next_index = {node.node_id: 0 for node in nodes}
        self.match_index = {node.node_id: 0 for node in nodes}
        self.leader_id = None

    def start_election(self):
        print(f"Node {self.node_id} starting election")
        self.state = 'candidate'
        self.term += 1
        self.voted_for = self.node_id
        votes = 1
        for node in self.nodes:
            if node.node_id != self.node_id:
                if node.request_vote(self.term, self.node_id):
                    votes += 1
        if votes > len(self.nodes) // 2:
            self.state = 'leader'
            self.leader_id = self.node_id
            print(f"Node {self.node_id} became the leader with term {self.term}")
            self.send_heartbeat()
        else:
            print(f"Node {self.node_id} failed to become the leader with term {self.term}")

    def request_vote(self, term, candidate_id):
        if term > self.term and (self.voted_for is None or self.voted_for == candidate_id):
            self.term = term
            self.voted_for = candidate_id
            print(f"Node {self.node_id} voted for {candidate_id} in term {term}")
            return True
        print(f"Node {self.node_id} rejected vote request from {candidate_id} in term {term}")
        return False

    def send_heartbeat(self):
        while self.state == 'leader':
            print(f"Leader {self.node_id} sending heartbeat")
            for node in self.nodes:
                if node.node_id != self.node_id:
                    node.append_entries(self.term, self.node_id, self.log)
            time.sleep(1)

    def append_entries(self, term, leader_id, entries):
        if term >= self.term:
            self.term = term
            self.state = 'follower'
            self.leader_id = leader_id
            self.log.extend(entries)
            print(f"Node {self.node_id} accepted entries from leader {leader_id} in term {term}")
            return True
        print(f"Node {self.node_id} rejected entries from leader {leader_id} in term {term}")
        return False

def simulate_attack_scenario():
    nodes = [Node(i, []) for i in range(5)]
    for node in nodes:
        node.nodes = nodes

    def attack_node_behavior(node):
        while True:
            node.term += 1
            print(f"Attack node {node.node_id} incrementing term to {node.term}")
            time.sleep(random.uniform(0.5, 1.5))

    attack_thread = threading.Thread(target=attack_node_behavior, args=(nodes[4],))
    attack_thread.start()

    leader_thread = threading.Thread(target=nodes[0].start_election)
    leader_thread.start()
    leader_thread.join()

if __name__ == "__main__":
    print("Simulating attack scenario:")
    simulate_attack_scenario()