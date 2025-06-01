from multiprocessing import Process
from pow_node import run_node

if __name__ == "__main__":
    peers = [("localhost", 5000), ("localhost", 5001), ("localhost", 5002),("localhost", 5003), ("localhost", 5004), ("localhost", 5005),("localhost", 5006), ("localhost", 5007), ("localhost", 5008), ("localhost", 5009)]
    
    # 正常ノードの数
    normal_nodes = [
        Process(target=run_node, args=(1, 5000, peers)),
        Process(target=run_node, args=(2, 5001, peers)),
        Process(target=run_node, args=(3, 5002, peers)),
        Process(target=run_node, args=(4, 5003, peers)),
        Process(target=run_node, args=(5, 5004, peers)),
        Process(target=run_node, args=(6, 5005, peers)),
        Process(target=run_node, args=(7, 5006, peers)),
        Process(target=run_node, args=(8, 5007, peers)),
        Process(target=run_node, args=(9, 5008, peers)),
        Process(target=run_node, args=(10, 5009, peers)),
    ]

    # 正常ノードの開始
    for node in normal_nodes:
        node.start()

    try:
        # 無限ループで実行を継続
        while True:
            pass
    except KeyboardInterrupt:
        # Ctrl+Cで停止した場合の処理
        print("Stopping processes...")
    finally:
        # 正常ノードの終了
        for node in normal_nodes:
            node.terminate()
            node.join()

    print("All processes stopped.")