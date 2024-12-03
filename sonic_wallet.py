from web3 import Web3
import time
import random
import requests
from web3.exceptions import TransactionNotFound
import json
from eth_account.messages import encode_defunct
from concurrent.futures import ThreadPoolExecutor
import threading

# Sonic Blaze Testnet Configuration
NETWORK_NAME = "Sonic Blaze Testnet"
RPC_URL = "https://rpc.blaze.soniclabs.com"
CHAIN_ID = 57054
CURRENCY_SYMBOL = "S"
FAUCET_API = "https://api.blaze.soniclabs.com/"

# 支持的代币类型及其合约地址
TOKEN_CONFIG = {
    "Sonic": {
        "symbol": "S",
        "contract": None,  # Sonic 是原生代币，不需要合约地址
        "decimals": 18
    },
    "Coral": {
        "symbol": "CORAL",
        "contract": "0xaf93888cbd250300470a1618206e036e11470149",  # Coral 代币合约地址
        "decimals": 18
    }
}

# 添加线程锁用于打印
print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)

def get_sign_message(proxy=None, token_type="Sonic"):
    """
    获取签名消息
    :param proxy: 代理设置
    :param token_type: 代币类型 (Sonic 或 Coral)
    :return: 签名消息
    """
    if token_type not in TOKEN_CONFIG:
        safe_print(f"❌ 不支持的代币类型: {token_type}")
        return None
        
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,fr;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://blaze.soniclabs.com',
        'referer': 'https://blaze.soniclabs.com/',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    
    data = {
        "operationName": "RequestTokens",
        "variables": {
            "symbol": token_type
        },
        "query": "mutation RequestTokens($symbol: String) {\n  requestTokens(symbol: $symbol)\n}"
    }
    
    try:
        if proxy:
            proxies = {
                "http": proxy['proxy_url'],
                "https": proxy['proxy_url']
            }
            response = requests.post(FAUCET_API, json=data, headers=headers, proxies=proxies, verify=False)
        else:
            response = requests.post(FAUCET_API, json=data, headers=headers)
            
        if response.status_code == 200:
            result = response.json()
            if 'data' in result and 'requestTokens' in result['data']:
                message = result['data']['requestTokens']
                safe_print(f"📝 {token_type}原始签名消息: {message}")
                # 提取签名消息中的哈希部分
                if '\n\n' in message:
                    hash_part = message.split('\n\n')[1]
                    safe_print(f"📝 {token_type}提取的哈希: {hash_part}")
                    return hash_part
                return message
            elif 'errors' in result:
                safe_print(f"❌ 获取{token_type}消息错误: {result['errors']}")
        return None
    except Exception as e:
        safe_print(f"❌ 获取{token_type}消息失败: {str(e)}")
        return None

def submit_signature(proxy, address, message, signature, token_type="Sonic"):
    """
    提交签名领取代币
    :param proxy: 代理设置
    :param address: 钱包地址
    :param message: 签名消息
    :param signature: 签名
    :param token_type: 代币类型 (Sonic 或 Coral)
    :return: 是否成功
    """
    if token_type not in TOKEN_CONFIG:
        safe_print(f"❌ 不支持的代币类型: {token_type}")
        return False
        
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,fr;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://blaze.soniclabs.com',
        'referer': 'https://blaze.soniclabs.com/',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    
    # 构建完整的签名消息
    full_message = f"Please sign following text to obtain 10 {token_type} tokens:\n\n{message}"
    safe_print(f"📝 完整签名消息: {full_message}")
    
    data = {
        "operationName": "ClaimTokens",
        "variables": {
            "address": address,
            "challenge": full_message,
            "signature": signature,
            "erc20Address": TOKEN_CONFIG[token_type]["contract"] if token_type != "Sonic" else None
        },
        "query": "mutation ClaimTokens($address: Address!, $challenge: String!, $signature: String!, $erc20Address: Address) {\n  claimTokens(\n    address: $address\n    challenge: $challenge\n    signature: $signature\n    erc20Address: $erc20Address\n  )\n}"
    }
    
    try:
        if proxy:
            proxies = {
                "http": proxy['proxy_url'],
                "https": proxy['proxy_url']
            }
            response = requests.post(FAUCET_API, json=data, headers=headers, proxies=proxies, verify=False)
        else:
            response = requests.post(FAUCET_API, json=data, headers=headers)
            
        safe_print(f"\n📬 {token_type}领取响应状态码: {response.status_code}")
        safe_print(f"📝 响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if 'data' in result and result['data'] is not None and 'claimTokens' in result['data']:
                safe_print(f"✨ {token_type}领取结果: {result['data']['claimTokens']}")
                return True
            elif 'errors' in result and result['errors']:
                error_msg = result['errors'][0].get('message', '未知错误')
                safe_print(f"❌ {token_type}领取错误: {error_msg}")
            else:
                safe_print("❌ 未知错误")
            return False
        return False
        
    except Exception as e:
        safe_print(f"❌ 提交{token_type}签名时出错: {str(e)}")
        return False

def sign_message(w3, message, private_key):
    message_encoded = encode_defunct(text=message)
    signed_message = w3.eth.account.sign_message(message_encoded, private_key=private_key)
    return signed_message.signature.hex()

def process_token(wallet, proxy, token_type):
    """
    处理单个代币的领取流程
    :param wallet: 钱包信息
    :param proxy: 代理信息
    :param token_type: 代币类型
    :return: 是否成功
    """
    try:
        # 创建Web3实例
        w3 = get_web3_with_proxy(proxy)
        if not w3:
            safe_print(f"❌ {token_type} Web3实例创建失败")
            return False
        
        # 查询领取前余额
        safe_print(f"\n📊 {token_type}领取前余额:")
        check_balance(w3, wallet['address'], token_type)
        
        # 获取签名消息
        safe_print(f"\n📝 正在获取{token_type}签名消息...")
        message = get_sign_message(proxy, token_type)
        if not message:
            safe_print(f"❌ 获取{token_type}签名消息失败")
            return False
        safe_print(f"✅ 获取{token_type}签名消息成功")
            
        # 签名消息
        safe_print(f"\n📝 正在签名{token_type}消息...")
        signature = sign_message(w3, message, wallet['private_key'])
        if not signature:
            safe_print(f"❌ {token_type}消息签名失败")
            return False
        safe_print(f"✅ {token_type}消息签名成功")
            
        # 提交签名领取测试币
        safe_print(f"\n🚀 正在提交签名领取{token_type}测试币...")
        if submit_signature(proxy, wallet['address'], message, signature, token_type):
            safe_print(f"✅ {token_type}测试币领取成功！")
            
            # 等待0.2秒让交易确认
            safe_print("⏳ 等待0.2秒确认交易...")
            time.sleep(0.2)
            
            # 查询领取后余额
            safe_print(f"\n📊 {token_type}领取后余额:")
            check_balance(w3, wallet['address'], token_type)
            
            return True
        else:
            safe_print(f"❌ {token_type}测试币领取失败")
            return False
            
    except Exception as e:
        safe_print(f"❌ 处理{token_type}时出错: {str(e)}")
        return False

def load_wallets(filename):
    wallets = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                if ':' in line:
                    address, private_key = line.strip().split(':')
                    wallets.append({
                        'address': address.strip(),
                        'private_key': private_key.strip()
                    })
        return wallets
    except UnicodeDecodeError:
        safe_print("文件编码错误，尝试其他编码...")
        with open(filename, 'r', encoding='gbk') as file:
            for line in file:
                if ':' in line:
                    address, private_key = line.strip().split(':')
                    wallets.append({
                        'address': address.strip(),
                        'private_key': private_key.strip()
                    })
        return wallets

def load_proxies(filename):
    proxies = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                # 解析格式：host:port:username:password
                parts = line.strip().split(':')
                if len(parts) == 4:
                    host, port, username, password = parts
                    proxy = {
                        'host': host,
                        'port': port,
                        'username': username,
                        'password': password,
                        'proxy_url': f"http://{username}:{password}@{host}:{port}"
                    }
                    proxies.append(proxy)
        safe_print(f"成功加载代理示例: {proxies[0]['host']}:{proxies[0]['port']}")
    except Exception as e:
        safe_print(f"加载代理出错: {str(e)}")
    return proxies

def test_proxy(proxy):
    try:
        # 禁用SSL警告
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 构建代理URL
        proxy_url = proxy['proxy_url']
        
        # 创建session并配置代理
        session = requests.Session()
        session.proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        # 配置session
        session.verify = False
        session.timeout = 10
        
        # 测试连接到一个可靠的网站
        test_url = "http://ip-api.com/json"
        response = session.get(test_url)
        if response.status_code == 200:
            ip_info = response.json()
            safe_print(f"✅ 代理连接成功 - IP: {ip_info.get('query', 'unknown')}")
            return True
        else:
            safe_print(f"❌ 代理连接失败: {response.status_code}")
            return False
    except Exception as e:
        safe_print(f"❌ 代理测试失败: {str(e)}")
        return False

def get_web3_with_proxy(proxy):
    try:
        # 首先测试代理
        if not test_proxy(proxy):
            safe_print("❌ 代理连接测试失败，跳过Web3连接")
            return None
            
        # 禁用SSL警告
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 构建代理URL
        proxy_url = proxy['proxy_url']
        
        # 创建session并配置代理
        session = requests.Session()
        session.proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        # 配置session
        session.verify = False
        session.timeout = 30
        
        # 创建自定义请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Connection': 'keep-alive'
        }
        session.headers.update(headers)
        
        # 测试RPC连接
        try:
            # 构建JSON-RPC请求
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
            }
            
            # 直接使用session发送请求
            response = session.post(RPC_URL, json=payload, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    block_number = int(result['result'], 16)
                    safe_print(f"✅ RPC连接成功，当前区块: {block_number}")
                    
                    # 创建Web3提供者
                    provider = Web3.HTTPProvider(
                        RPC_URL,
                        request_kwargs={
                            "proxies": session.proxies,
                            "verify": False,
                            "timeout": 30,
                            "headers": headers
                        }
                    )
                    
                    # 初始化Web3
                    w3 = Web3(provider)
                    return w3
            
            safe_print(f"❌ RPC连接失败: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            safe_print(f"❌ RPC连接失败: {str(e)}")
            return None
            
    except Exception as e:
        safe_print(f"❌ Web3连接失败: {str(e)}")
        return None

def check_balance(w3, wallet_address, token_type="Sonic"):
    """
    查询钱包余额
    :param w3: Web3实例
    :param wallet_address: 钱包地址
    :param token_type: 代币类型
    :return: 是否成功
    """
    try:
        if token_type not in TOKEN_CONFIG:
            safe_print(f"❌ 不支持的代币类型: {token_type}")
            return False
            
        token_info = TOKEN_CONFIG[token_type]
        if token_info["contract"] is None:
            # 查询原生代币余额
            balance = w3.eth.get_balance(wallet_address)
            balance_in_ether = w3.from_wei(balance, 'ether')
            safe_print(f"💰 当前{token_type}余额: {balance_in_ether} {token_info['symbol']}")
        else:
            # 查询代币余额
            # 代币的 ABI
            token_abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                }
            ]
            
            # 创建合约实例
            token_contract = w3.eth.contract(
                address=w3.to_checksum_address(token_info["contract"]), 
                abi=token_abi
            )
            
            # 查询余额
            balance = token_contract.functions.balanceOf(wallet_address).call()
            balance_formatted = balance / (10 ** token_info["decimals"])
            safe_print(f"💰 当前{token_type}余额: {balance_formatted} {token_info['symbol']}")
            
        return True
    except Exception as e:
        safe_print(f"❌ 查询{token_type}余额失败: {str(e)}")
        return False

def process_wallet(wallet, proxies, start_proxy_index=0):
    """
    处理单个钱包的所有代币领取，如果代理失败会尝试下一个代理
    :param wallet: 钱包信息
    :param proxies: 代理列表
    :param start_proxy_index: 开始尝试的代理索引
    :return: (bool, int) 元组，表示是否成功和使用的代理索引
    """
    total_proxies = len(proxies)
    proxy_index = start_proxy_index
    
    while proxy_index < total_proxies:
        proxy = proxies[proxy_index]
        safe_print(f"\n处理钱包 {wallet['address']} 使用代理 {proxy['host']}:{proxy['port']}")
        safe_print(f"当前代理索引: {proxy_index + 1}/{total_proxies}")
        
        all_success = True
        
        # 处理每种代币
        for token_type in TOKEN_CONFIG:
            safe_print(f"\n🎯 开始处理 {token_type} 代币")
            if not process_token(wallet, proxy, token_type):
                safe_print(f"❌ {token_type}处理失败，尝试下一个代理")
                all_success = False
                break
            
            # 在处理不同代币之间添加随机延迟
            if token_type != list(TOKEN_CONFIG.keys())[-1]:  # 如果不是最后一种代币
                delay = random.uniform(0.1, 0.2)
                safe_print(f"⏳ 等待 {delay:.1f} 秒后处理下一种代币...")
                time.sleep(delay)
        
        if all_success:
            return True, proxy_index
        
        proxy_index += 1
        continue
            
    safe_print(f"❌ 已尝试所有可用代理({total_proxies}个)，钱包处理失败")
    return False, proxy_index

def main():
    try:
        # 加载钱包和代理
        safe_print(f"\n📝 正在加载钱包...")
        wallets = load_wallets('wallets.txt')
        if not wallets:
            safe_print("❌ 没有找到钱包或钱包文件为空")
            return
        safe_print(f"✅ 已加载 {len(wallets)} 个钱包")
        
        safe_print(f"\n📝 正在加载代理...")
        proxies = load_proxies('proxies.txt')
        if not proxies:
            safe_print("❌ 没有找到代理或代理文件为空")
            return
        safe_print(f"✅ 已加载 {len(proxies)} 个代理")
        
        # 创建线程池，设置最大并发数
        max_workers = 10  # 可以根据需要调整并发数
        successful_wallets = 0
        failed_wallets = []
        
        def process_wallet_wrapper(args):
            i, wallet = args
            safe_print(f"\n🔄 处理钱包 {i}/{len(wallets)}")
            success, _ = process_wallet(wallet, proxies, random.randint(0, len(proxies)-1))
            return wallet['address'], success

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(process_wallet_wrapper, enumerate(wallets, 1)))
            
        # 统计结果
        for wallet_address, success in results:
            if success:
                successful_wallets += 1
            else:
                failed_wallets.append(wallet_address)
        
        # 打印统计信息
        safe_print(f"\n📊 任务完成统计:")
        safe_print(f"✅ 成功处理: {successful_wallets}/{len(wallets)} 个钱包")
        if failed_wallets:
            safe_print(f"❌ 失败钱包列表:")
            for addr in failed_wallets:
                safe_print(f"  - {addr}")
                
    except Exception as e:
        safe_print(f"❌ 程序执行出错: {str(e)}")
        return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        safe_print("\n\n⚠️ 程序被用户中断")
    except Exception as e:
        safe_print(f"\n\n❌ 程序异常退出: {str(e)}")
    finally:
        safe_print("\n程序结束")
