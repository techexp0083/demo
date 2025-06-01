import hashlib
import time
import socket
import threading
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class Block:
    def __init__(self, index, previous_hash, timestamp, data, nonce, hash_value=None):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.nonce = nonce
        self.hash = hash_value if hash_value else self.calculate_hash()

    def calculate_hash(self):
        sha = hashlib.sha256()
        sha.update(f"{self.index}{self.previous_hash}{self.timestamp}{self.data}{self.nonce}".encode('utf-8'))
        return sha.hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "data": self.data,
            "nonce": self.nonce,
            "hash": self.hash
        }

class Node:
    def __init__(self, node_id, port):
        self.node_id = node_id
        self.port = port
        self.chain = [self.create_genesis_block()]
        self.peers = []

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("0.0.0.0", port))
        self.server.listen(5)
        logging.info(f"Listening on port {port}")

    def create_genesis_block(self):
        # 固定されたジェネシスブロックの値
        index = 0
        previous_hash = "0"
        timestamp = 0  # 固定されたタイムスタンプ
        data = "Genesis Block"
        nonce = 0
        hash_value = "0000000000000000000000000000000000000000000000000000000000000000"  # 固定されたハッシュ値
        return Block(index, previous_hash, timestamp, data, nonce, hash_value)

    def add_peer(self, peer_address):
        self.peers.append(peer_address)

    def handle_client(self, client_socket):
        request = client_socket.recv(1024).decode('utf-8')
        logging.info(f"Received: {request} from {client_socket.getpeername()}")
        if request.startswith("NEW_BLOCK"):
            self.handle_new_block(request)
        elif request.startswith("GET_CHAIN"):
            self.send_chain(client_socket)
        client_socket.close()

    def handle_new_block(self, request):
        parts = request.split(":")
        index = int(parts[1])
        previous_hash = parts[2]
        timestamp = float(parts[3])
        data = parts[4]
        nonce = int(parts[5])
        received_hash = parts[6]
        new_block = Block(index, previous_hash, timestamp, data, nonce)

        if self.is_valid_new_block(new_block, self.chain[-1], received_hash):
            self.chain.append(new_block)
            logging.info(f"New block added: {new_block.hash}")
            self.print_blockchain()
        else:
            logging.warning(f"Invalid block received with hash: {received_hash}")

    def is_valid_new_block(self, new_block, previous_block, received_hash):
        if previous_block.index + 1 != new_block.index:
            logging.warning(f"Invalid index: {new_block.index}")
            return False
        if previous_block.hash != new_block.previous_hash:
            logging.warning(f"Invalid previous hash: {new_block.previous_hash}")
            return False
        if new_block.calculate_hash() != received_hash:
            logging.warning(f"Invalid hash: {received_hash}")
            return False
        if not received_hash.startswith("0000"):  # 難易度を確認
            logging.warning(f"Hash does not meet difficulty: {received_hash}")
            return False
        return True

    def start_server(self):
        while True:
            client_socket, addr = self.server.accept()
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()

    def mine_block(self, data):
        self.sync_chain()  # マイニング前にチェーンを同期
        previous_block = self.chain[-1]
        index = previous_block.index + 1
        timestamp = time.time()
        nonce = 0

        start_time = time.time()  # マイニング開始時刻
        while True:
            new_block = Block(index, previous_block.hash, timestamp, data, nonce)
            if new_block.hash.startswith("0000"):  # 難易度を調整
                break
            nonce += 1
        end_time = time.time()  # マイニング終了時刻

        self.chain.append(new_block)
        logging.info(f"Block mined: {new_block.hash} in {end_time - start_time} seconds")
        self.broadcast_new_block(new_block)
        time.sleep(5)  # 5秒待機
        self.print_blockchain()  # ブロックチェーンの状態を出力

    def broadcast_new_block(self, new_block):
        for peer in self.peers:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            retry_count = 0
            while retry_count < 5:
                try:
                    client.connect((peer[0], peer[1]))  # 修正: peerをタプル形式で渡す
                    message = f"NEW_BLOCK:{new_block.index}:{new_block.previous_hash}:{new_block.timestamp}:{new_block.data}:{new_block.nonce}:{new_block.hash}"
                    client.send(message.encode('utf-8'))
                    client.close()
                    logging.info(f"Broadcasted new block to {peer}")
                    break
                except ConnectionRefusedError:
                    logging.warning(f"Connection refused to {peer}. Retrying...")
                    retry_count += 1
                    time.sleep(1)  # 1秒待機して再試行

    def send_chain(self, client_socket):
        chain_data = [block.to_dict() for block in self.chain]
        client_socket.send(json.dumps(chain_data).encode('utf-8'))

    def sync_chain(self):
        longest_chain = self.chain
        for peer in self.peers:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client.connect((peer[0], peer[1]))  # 修正: peerをタプル形式で渡す
                client.send("GET_CHAIN".encode('utf-8'))
                response = client.recv(4096).decode('utf-8')
                peer_chain = json.loads(response)
                peer_blocks = [Block(index=block['index'], previous_hash=block['previous_hash'], timestamp=block['timestamp'], data=block['data'], nonce=block['nonce'], hash_value=block['hash']) for block in peer_chain]
                if len(peer_blocks) > len(longest_chain) and self.is_valid_chain(peer_blocks):
                    longest_chain = peer_blocks
                client.close()
            except ConnectionRefusedError:
                logging.warning(f"Connection refused to {peer}. Skipping...")
        self.chain = longest_chain
        logging.info("Blockchain updated with the latest valid chain from peers.")
        self.print_blockchain()

    def is_valid_chain(self, chain):
        if chain[0].hash != self.chain[0].hash:
            return False
        for i in range(1, len(chain)):
            if not self.is_valid_new_block(chain[i], chain[i-1], chain[i].hash):
                return False
        return True

    def print_blockchain(self):
        logging.info("Current Blockchain:")
        for block in self.chain:
            logging.info(f"Index: {block.index}, Hash: {block.hash}, Previous Hash: {block.previous_hash}, Data: {block.data}")

def run_node(node_id, port, peers):
    node = Node(node_id=node_id, port=port)
    for peer in peers:
        node.add_peer(peer)
    server_thread = threading.Thread(target=node.start_server)
    server_thread.start()

    # Simulate mining a block and syncing the chain
    while True:
        node.mine_block("Some transaction data")
        time.sleep(10)  # 10秒待機して次のブロックをマイニング