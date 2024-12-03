# 安装web3库
# pip install web3

from web3 import Web3

# 生成新的钱包
def create_wallet():
    # 创建Web3实例，连接到本地节点（或使用Infura等服务）
    w3 = Web3()  # 这里可以添加连接参数，例如 Web3(Web3.HTTPProvider('https://your.infura.endpoint'))
    
    # 创建一个新的账户
    account = w3.eth.account.create()  # 直接创建账户
    address = w3.to_checksum_address(account.address)  # 获取地址并转换为checksum格式
    private_key = account._private_key.hex()  # 获取私钥，使用_private_key
    
    return address, private_key

# 保存钱包到文件
def save_wallets_to_file(wallets, filename):
    with open(filename, 'w') as f:
        for address, private_key in wallets:
            f.write(f"{address}:{private_key}\n")  # 格式为 "地址:私钥"

# 使用示例
if __name__ == "__main__":
    num_wallets = int(input("请输入要创建的钱包数量: "))  # 用户输入钱包数量
    wallets = [create_wallet() for _ in range(num_wallets)]  # 创建指定数量的钱包
    save_wallets_to_file(wallets, 'wallets.txt')  # 保存到文件
    print(f"{num_wallets} 个钱包已创建并保存到 wallets.txt")
