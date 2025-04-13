from pymilvus import connections, utility


def test_milvus_connection():
    try:
        # 连接到Milvus服务器
        connections.connect(
            alias="default",
            host="localhost",
            port="19530"
        )
        print("Milvus连接成功！")

        # 获取Milvus服务器版本
        print(f"Milvus版本: {utility.get_server_version()}")

        return True
    except Exception as e:
        print(f"Milvus连接失败: {e}")
        return False


if __name__ == "__main__":
    test_milvus_connection()