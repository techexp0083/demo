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
        self.leader_id = None
        self.leader_missing =0
        self.runnning = True

    def main_loop(self):
        while(self.runnning):
            if self.state == 'leader':
                self.leader_activity()
            else:
                self.follower_activity()
            time.sleep(random.uniform(1,1.5))
        print(f"Node {self.node_id} stopped.")

    def leader_activity(self):
        choice = random.randrange(0,2)
        if choice == 0:
            print(f"Node {self.node_id} failed to send heartbeat")
        else:
            self.send_heartbeat()

    def follower_activity(self):
        # HertBeatの喪失検出処理
        if self.node_id == 0:
            print(f"Node {self.node_id} hasn't touched {self.leader_missing} cycles.")
        self.leader_missing += 1
        if self.leader_missing > 2:
            print(f"Node {self.node_id} lost the leader")
            self.leader_missing = 0
            self.start_election()

    def start_election(self):
        print(f"Node {self.node_id} starting election")
        self.state = 'candidate'
        self.term += 1
        self.voted_for = self.node_id
        votes = 1
        for node in self.nodes:
            if node.node_id != self.node_id:
                result = node.request_vote(self.term, self.node_id)
                if result[1] > self.term:
                    # 自身のTermが周囲より遅延しているとき、自身の情報を最新化する必要がある。
                    # Followerになり、HertBeatでのAppendを期待する。
                    print(f"Node {self.node_id} give up election for term {self.term} ")
                    self.state = 'follower'
                    self.leader_missing = 0
                    self.leader_id = None
                    self.term = result[1]
                if result[0]:
                    votes += 1
        if votes > len(self.nodes) // 2:
            self.state = 'leader'
            self.leader_id = self.node_id
            print(f"Node {self.node_id} became the leader with term {self.term}")
            self.leader_activity()
        else:
            print(f"Node {self.node_id} failed to become the leader with term {self.term}")

    def request_vote(self, term, candidate_id):
        if term > self.term :
            self.term = term
            self.voted_for = candidate_id
            print(f"Node {self.node_id} voted for {candidate_id} in term {term}")
            self.leader_missing = 0
            return (True , self.term)
        elif term == self.term and self.voted_for == candidate_id:
            self.voted_for = candidate_id
            print(f"Node {self.node_id} re-voted for {candidate_id} in term {term}")
            self.leader_missing = 0
            return (True , self.term)
        print(f"Node {self.node_id} rejected vote request from {candidate_id} in term {term}")
        return (False, self.term)

    def send_heartbeat(self):
        print(f"Node {self.node_id} sending heartbeat")
        for node in self.nodes:
            if node.node_id != self.node_id:
                node.append_entries(self.term, self.node_id, self.log)

    def append_entries(self, term, leader_id, entries):
        self.leader_missing = 0
        if term >= self.term:
            self.term = term
            self.state = 'follower'
            self.leader_id = leader_id
            self.log.extend(entries)
            print(f"Node {self.node_id} accepted entries from leader {leader_id} in term {term}")
            return True
        print(f"Node {self.node_id} rejected entries from leader {leader_id} in term {term}")
        return False

class AttackNode(Node):
    def follower_activity(self):
        print(f"Node {self.node_id} executing usurpation!!!")
        self.start_election()


def simulate_attack_scenario():
    nodes = [Node(i, []) for i in range(5)]
    threds = []
    nodes[4] = AttackNode(4, [])
    for node in nodes:
        node.nodes = nodes
        threds.append(threading.Thread(target=node.main_loop))


    try :
        for thred in threds:
            thred.start()
        print("Simulation started.")
        for thread in threds:
            thread.join()
    except KeyboardInterrupt:
        print("Simulation stopping...")
        for node in nodes:
            node.runnning = False
        for thread in threds:
            thread.join(timeout = 2)
        raise
if __name__ == "__main__":
    print("Simulating attack scenario:")
    simulate_attack_scenario()