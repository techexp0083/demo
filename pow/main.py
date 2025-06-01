from multiprocessing import Process
from pow_node import run_node

if __name__ == "__main__":
    peers = [("localhost", 5000), ("localhost", 5001), ("localhost", 5002)]
    
    # 正常ノードの数
    normal_nodes = [
        Process(target=run_node, args=(1, 5000, peers)),
        Process(target=run_node, args=(2, 5001, peers)),
        Process(target=run_node, args=(3, 5002, peers))
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