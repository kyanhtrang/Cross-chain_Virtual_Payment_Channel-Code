import json
import time

import eth_keys
import numpy as np
from eth_account.messages import encode_defunct
from eth_utils import decode_hex
from web3 import Web3


def getPublicKey(val):
  msg='abc'
  message=encode_defunct(text=msg)
  sign_message=web3.eth.account.sign_message(message,private_key=val)
  k=web3.eth.account.recover_message(message,signature=sign_message.signature)
  return k
def to_32byte_hex(val):
        return web3.to_hex(web3.to_bytes(val).rjust(32,b'\0'))

# Kết nối tập tin .sol
with open('.\ETH\helloworld_sol_Greeter.abi', 'r') as f:
    abi = json.load(f)
with open('.\ETH\helloworld_sol_Greeter.bin', 'r') as f:
    code = f.read()

with open('.\ETH\committee1_sol_committee.abi', 'r') as f:
    abi_2 = json.load(f)
with open('.\ETH\committee1_sol_committee.bin', 'r') as f:
    code_2 = f.read()


# Kiểm tra kết nối với ganache
web3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
print(web3.is_connected())

# Lấy khóa chung của Ingrid, 3 người dùng
Ingrid = web3.eth.accounts[5]
Ingrid_privateKey = eth_keys.keys.PrivateKey(decode_hex('ac9124d290c659500d4e6beb043aa8674a6a8757f6b6034f32f3b15d21da8ace'))
Ingrid_publicKey = getPublicKey(Ingrid_privateKey)
print('Ingrid_publicKey******:',Ingrid_publicKey)
Bob = web3.eth.accounts[6]
Bob_privateKey = eth_keys.keys.PrivateKey(decode_hex('db8048b9033ad279f02c3e84bd221ee210af84e27629f47279b0aaf5ea273f53'))
Bob_publicKey = getPublicKey(Bob_privateKey)

# Triển khai hợp đồng thông minh xây dựng kênh ảo
def Deployment_channel_contract():
  global Channels
  Greeter = web3.eth.contract(bytecode=code,abi=abi)
  option = {"from": Ingrid, "gas": 3000000}
  tx_hash = Greeter.constructor().transact(option)
  tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
  contract_address = web3.to_checksum_address(tx_receipt.contractAddress)
  print("channel_contract_address:", contract_address)
  # Sau đó sử dụng Channel để gọi các chức năng hợp đồng thông minh
  Channels = web3.eth.contract(contract_address,abi=abi)

Voter_1 = web3.eth.accounts[7]
Voter_2 = web3.eth.accounts[8]
Voter_3 = web3.eth.accounts[9]
# Triển khai hợp đồng thông minh
def Deployment_committee_contract():
  committee = web3.eth.contract(bytecode=code_2, abi=abi_2)
  option_2 = {"from": Voter_1, "gas": 3000000}
  tx_hash_2 = committee.constructor().transact(option_2)
  tx_receipt_2 = web3.eth.wait_for_transaction_receipt(tx_hash_2)
  committee_contract_address = web3.to_checksum_address(tx_receipt_2.contractAddress)
  print("committee_contract_address:", committee_contract_address)
  return committee_contract_address

count=0
message=[] # Mảng thông minh
message_Ingrid=[]
sign_message_Ingrid=[]
ec_Ingrid_hash=[]
ec_Ingrid_v=[]
ec_Ingrid_r=[]
ec_Ingrid_s=[]
message_b=[]
sign_message_b=[]
ec_b_hash=[]
ec_b_v=[]
ec_b_r=[]
ec_b_s=[]
total_amount=0#Tổng số tiền đã chuyển
total_amount_all=[]#Số tiền chuyển mỗi lần


# Tạo kênh thanh toán
def deploy_lc(Ingrid,Bob,value):
  # Cả hai bên đều chuyển tiền vào hợp đồng thông minh và giá trị chính là số tiền.
  tx_hash = Channels.functions.pay().transact({"from":Ingrid,"value":value})
  tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
  tx_hash2 = Channels.functions.pay().transact({"from":Bob,"value":value})
  tx_receipt2 = web3.eth.wait_for_transaction_receipt(tx_hash2)
  # Lưu khóa công khai
  tx_hash3 = Channels.functions.saveAccount_publickey(Ingrid_publicKey,Bob_publicKey).transact({"from":Ingrid,"value":value})
  tx_receipt3 = web3.eth.wait_for_transaction_receipt(tx_hash3)
  # Lưu địa chỉ
  tx_hash4 = Channels.functions.saveAccount(Ingrid,Bob).transact({"from":Ingrid,"value":value})
  tx_receipt4 = web3.eth.wait_for_transaction_receipt(tx_hash4) 
  #Tính toán chi phí
  costs = tx_receipt.gasUsed + tx_receipt2.gasUsed
  # costs=tx_receipt.gasUsed+tx_receipt2.gasUsed+tx_receipt3.gasUsed+tx_receipt4.gasUsed
  print( "lc deploy cost: ",costs)

# Cập nhật kênh thanh toán
def update_lc(value=0):
  global count
  count = count + 1
  message.append('Number:count'+str(count)+'Ingrid.balance:'+ str(~value)+'Bob.balance:'+str(value))
  message_Ingrid.append(encode_defunct(text=message[count-1]))
  sign_message_Ingrid.append(web3.eth.account.sign_message(message_Ingrid[count-1], private_key = Ingrid_privateKey))
  ec_recover_args_a = (msghash,v,r,s)=(web3.to_hex(sign_message_Ingrid[count-1].messageHash),sign_message_Ingrid[count-1].v,
            to_32byte_hex(sign_message_Ingrid[count-1].r),to_32byte_hex(sign_message_Ingrid[count-1].s))
  ec_Ingrid_hash.append(ec_recover_args_a[0])
  ec_Ingrid_v.append(ec_recover_args_a[1])
  ec_Ingrid_r.append(ec_recover_args_a[2])
  ec_Ingrid_s.append(ec_recover_args_a[3])
  message_b.append(encode_defunct(text=message[count-1]))
  sign_message_b.append(web3.eth.account.sign_message(message_b[count-1],private_key=Bob_privateKey))
  ec_recover_args_b=(msghash,v,r,s)=(web3.to_hex(sign_message_b[count-1].messageHash),sign_message_b[count-1].v,
            to_32byte_hex(sign_message_b[count-1].r),to_32byte_hex(sign_message_b[count-1].s))
  ec_b_hash.append(ec_recover_args_b[0])
  ec_b_v.append(ec_recover_args_b[1])
  ec_b_r.append(ec_recover_args_b[2])
  ec_b_s.append(ec_recover_args_b[3])

# Đóng kênh thanh toán (trường hợp optimistic)
def close_lc(value):
  load_count_a = 1
  tx_hash = Channels.functions.submit_transaction_a(load_count_a,value,value,ec_b_hash[load_count_a-1],ec_b_v[load_count_a-1],
            ec_b_r[load_count_a-1],ec_b_s[load_count_a-1], 30).transact({"from":Ingrid,"value":0})
  tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
  load_count_b=1
  tx_hash2 = Channels.functions.submit_transaction_b(load_count_b,value,value,ec_Ingrid_hash[load_count_b-1],ec_Ingrid_v[load_count_b-1],
            ec_Ingrid_r[load_count_b-1],ec_Ingrid_s[load_count_b-1],Ingrid,Bob).transact({"from":Bob,"value":0})
  tx_receipt2 = web3.eth.wait_for_transaction_receipt(tx_hash2)
  print("lc optimistic closed cost : ",tx_receipt.gasUsed + tx_receipt2.gasUsed)

# Đóng kênh thanh toán (trường hợp pessimistic)
def close_lc_pessimistic(value):
  load_count_a = 1
  load_count_b = 1
  cvc_count_b = 2
  tx_hash = Channels.functions.submit_transaction_a(load_count_a,value,value,ec_b_hash[load_count_a-1],ec_b_v[load_count_a-1],
            ec_b_r[load_count_a-1],ec_b_s[load_count_a-1],30).transact({"from":Ingrid,"value":0})
  tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
  tx_hash1 = Channels.functions.check_cvc_Validity(ec_a_hash_cvc[cvc_count_b-1],ec_a_v_cvc[cvc_count_b-1],
            ec_a_r_cvc[cvc_count_b-1],ec_a_s_cvc[cvc_count_b-1]).transact({"from":Ingrid,"value":0})
  tx_receipt1 = web3.eth.wait_for_transaction_receipt(tx_hash1)
  tx_hash2 = Channels.functions.submit_transaction_b(load_count_b,value,value,ec_Ingrid_hash[load_count_b-1],
            ec_Ingrid_v[load_count_b-1],ec_Ingrid_r[load_count_b-1],ec_Ingrid_s[load_count_b-1],Ingrid,Bob).transact({"from":Bob,"value":0})
  tx_receipt2=web3.eth.wait_for_transaction_receipt(tx_hash2)
  print("lc pessimistic closed cost : ",tx_receipt.gasUsed+tx_receipt1.gasUsed+tx_receipt2.gasUsed)

def get_balance(account):
  print(1)
  tx_hash=Channels.functions.getBalance1(account).call()
  tx_receipt=web3.eth.wait_for_transaction_receipt(tx_hash)
  print(tx_receipt)

message_cvc = []
cvc_Ingrid_balance = 0
cvc_Bob_balance = 0
cvc_count = 0   # 指示message_vc[]的数组下标
cvc_OpenMessage_Ingrid = []
sign_cvc_OpenMessage_Ingrid = [] # 保存ingrid签名后的信息
message_b_cvc = []
sign_cvc_OpenMessage_Bob = []
ec_a_hash_cvc = []
ec_a_v_cvc = []
ec_a_r_cvc = []
ec_a_s_cvc = []
ec_b_hash_cvc = []
ec_b_v_cvc = []
ec_b_r_cvc = []
ec_b_s_cvc = []

# Mở kênh ảo cross-chain
def deploy_cvc(Ingrid,Bob,value,time_cvc):
  # Số tiền hai bên khóa
  global cvc_Ingrid_balance
  global cvc_Bob_balance
  global cvc_count
  cvc_Ingrid_balance=value
  cvc_Bob_balance=value
  # Tạo thông tin kênh ảo cross-chain
  message_cvc.append("open a virtual channel with initial balance Ingrid"+str(cvc_Ingrid_balance)+"Bob"+str(cvc_Bob_balance))
  cvc_OpenMessage_Ingrid.append(encode_defunct(text=message_cvc[cvc_count]))
  # Thông tin khóa chữ ký
  start = time.time()
  a = web3.eth.account.sign_message(cvc_OpenMessage_Ingrid[cvc_count],private_key=Ingrid_privateKey)
  print("a",a)
  end = time.time()
  Times.append(end-start)
  print("sign_time", end-start)
  sign_cvc_OpenMessage_Ingrid.append(a)

  start = time.time()
  b = web3.eth.account.recover_message(cvc_OpenMessage_Ingrid[cvc_count], signature ='0x36e5a520780a16f5804c8036c470f7a8938fca54768cce5d577a72e5a35c5df92befd39f50a826cf594c5555949b29913ad2076fe57a9801d11c54bd839aac161c')
  end = time.time()
  print("Thời gian xác minh：****", end-start)
  print('Ingrid_publicKey******:',Ingrid_publicKey)
  print("Địa chỉ：*******", b)


  # Tính toán kích thước của các tin nhắn kênh ảo cross-chain mở (Ingrid)
  CVC_Open_Message_Signed_by_Ingrid_bytes = len(web3.to_hex(sign_cvc_OpenMessage_Ingrid[cvc_count].signature))/2
  print("CVC_Open_Message_Signed_by_Ingrid_hex",web3.to_hex(sign_cvc_OpenMessage_Ingrid[cvc_count].signature))
  print("CVC_Open_Message_Signed_by_Ingrid_bytes:",CVC_Open_Message_Signed_by_Ingrid_bytes)
  
  # Lấy hàm băm, v, r, s trong thông tin chữ ký (chủ yếu chuyển cho hợp đồng thông minh để xác minh chữ ký nhằm tạo điều kiện xác minh chữ ký hợp đồng thông minh)
  ec_recover_args_a_cvc=(msghash,v,r,s)=(web3.to_hex(sign_cvc_OpenMessage_Ingrid[cvc_count].messageHash),sign_cvc_OpenMessage_Ingrid[cvc_count].v,
            to_32byte_hex(sign_cvc_OpenMessage_Ingrid[cvc_count].r),to_32byte_hex(sign_cvc_OpenMessage_Ingrid[cvc_count].s))
  ec_a_hash_cvc.append(ec_recover_args_a_cvc[0])
  ec_a_v_cvc.append(ec_recover_args_a_cvc[1]) 
  ec_a_r_cvc.append(ec_recover_args_a_cvc[2])
  ec_a_s_cvc.append(ec_recover_args_a_cvc[3])

  message_b_cvc.append(encode_defunct(text=message_cvc[cvc_count]))
  sign_cvc_OpenMessage_Bob.append(web3.eth.account.sign_message(message_b_cvc[cvc_count],private_key=Bob_privateKey))
  
  # Tính toán kích thước của các tin nhắn kênh ảo cross-chain mở (Ingrid)
  CVC_Open_Message_Signed_by_Bob_bytes = len(web3.to_hex(sign_cvc_OpenMessage_Bob[cvc_count].signature))/2
  print("CVC_Open_Message_Signed_by_Bob_hex",web3.to_hex(sign_cvc_OpenMessage_Bob[cvc_count].signature))
  print("CVC_Open_Message_Signed_by_Bob_bytes:",CVC_Open_Message_Signed_by_Bob_bytes)

  # Lấy hàm băm, v, r, s trong thông tin chữ ký (chủ yếu chuyển cho hợp đồng thông minh để xác minh chữ ký nhằm tạo điều kiện xác minh chữ ký hợp đồng thông minh)
  ec_recover_args_b_cvc=(msghash,v,r,s)=(web3.to_hex(sign_cvc_OpenMessage_Bob[cvc_count].messageHash),sign_cvc_OpenMessage_Bob[cvc_count].v,
            to_32byte_hex(sign_cvc_OpenMessage_Bob[cvc_count].r),to_32byte_hex(sign_cvc_OpenMessage_Bob[cvc_count].s))
  ec_b_hash_cvc.append(ec_recover_args_b_cvc[0])
  ec_b_v_cvc.append(ec_recover_args_b_cvc[1])
  ec_b_r_cvc.append(ec_recover_args_b_cvc[2])
  ec_b_s_cvc.append(ec_recover_args_b_cvc[3])
  # Gửi chữ ký vào hợp đồng thông minh
  # tx_hash=Channels.functions.open_cvc(ec_a_hash_cvc[0],ec_a_v_cvc[0],ec_a_r_cvc[0],ec_a_s_cvc[0],time_cvc,ec_b_hash_cvc[0],
  #           ec_b_v_cvc[0],ec_b_r_cvc[0],ec_b_s_cvc[0]).transact({"from":Ingrid,"value":value})
  # tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
  print("cvc open...")


# Cập nhật kênh ảo
def update_cvc(value):
  global cvc_count
  cvc_count=cvc_count+1
  message_cvc.append('Number:count'+str(cvc_count)+'accounta.balance:'+str(~value)+'accountb.balance:'+str(value))
  cvc_OpenMessage_Ingrid.append(encode_defunct(text=message_cvc[cvc_count]))
  sign_cvc_OpenMessage_Ingrid.append(web3.eth.account.sign_message(cvc_OpenMessage_Ingrid[cvc_count],private_key=Ingrid_privateKey))
  ec_recover_args_a_cvc=(msghash,v,r,s)=(web3.to_hex(sign_cvc_OpenMessage_Ingrid[cvc_count].messageHash),sign_cvc_OpenMessage_Ingrid[cvc_count].v,
            to_32byte_hex(sign_cvc_OpenMessage_Ingrid[cvc_count].r),to_32byte_hex(sign_cvc_OpenMessage_Ingrid[cvc_count].s))
  ec_a_hash_cvc.append(ec_recover_args_a_cvc[0])
  ec_a_v_cvc.append(ec_recover_args_a_cvc[1])
  ec_a_r_cvc.append(ec_recover_args_a_cvc[2])
  ec_a_s_cvc.append(ec_recover_args_a_cvc[3])
  message_b_cvc.append(encode_defunct(text=message_cvc[cvc_count]))
  sign_cvc_OpenMessage_Bob.append(web3.eth.account.sign_message(message_b_cvc[cvc_count],private_key=Bob_privateKey))
  ec_recover_args_b_cvc=(msghash,v,r,s)=(web3.to_hex(sign_cvc_OpenMessage_Bob[cvc_count].messageHash),sign_cvc_OpenMessage_Bob[cvc_count].v,
            to_32byte_hex(sign_cvc_OpenMessage_Bob[cvc_count].r),to_32byte_hex(sign_cvc_OpenMessage_Bob[cvc_count].s))
  ec_b_hash_cvc.append(ec_recover_args_b_cvc[0])
  ec_b_v_cvc.append(ec_recover_args_b_cvc[1])
  ec_b_r_cvc.append(ec_recover_args_b_cvc[2])
  ec_b_s_cvc.append(ec_recover_args_b_cvc[3])
  print("cvc update...")

# Đóng kênh ảo cross-chain trong các trường hợp bất thường (trường hợp đầu tiên)
def close_cvc(value):
  cvc_count_a=2
  cvc_count_b=2
  # tx_hash = Channels.functions.submit_close_cvc(value,value,ec_a_hash_cvc[cvc_count_b-1],ec_a_v_cvc[cvc_count_b-1],ec_a_r_cvc[cvc_count_b-1],
  #           ec_a_s_cvc[cvc_count_b-1],ec_b_hash_cvc[cvc_count_a-1],ec_b_v_cvc[cvc_count_a-1],ec_b_r_cvc[cvc_count_a-1],
  #           ec_b_s_cvc[cvc_count_a-1]).transact({"from":Ingrid,"value":0})
  # tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
  print("cvc close...")

def close_cvc_abnormal(committeeAddress,transactionId,Ingrid_and_Bob_Balance, zero, value):
  cvc_count_a=2
  # ingrid提交OCb 和 CCi
  tx_hash=Channels.functions.close_cvc_abnormal(ec_b_hash_cvc[0],ec_b_v_cvc[0],ec_b_r_cvc[0],ec_b_s_cvc[0],ec_a_hash_cvc[cvc_count_a-1],
            ec_a_v_cvc[cvc_count_a-1],ec_a_r_cvc[cvc_count_a-1],ec_a_s_cvc[cvc_count_a-1]).transact({"from":Ingrid,"value":0})
  tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash) # view 0 gas
  # Khởi động bỏ phiếu
  print("voting.........")
  committee(1,3000000000000000000)
  # Phân bổ số dư dựa trên kết quả biểu quyết
  tx_hash1 = Channels.functions.close_cvc_abnormal_1(committeeAddress,transactionId,Ingrid_and_Bob_Balance,zero).transact({"from":Ingrid,"value":value})
  tx_receipt1 = web3.eth.wait_for_transaction_receipt(tx_hash1)
  print("close_cvc_abnomal cost : ", tx_receipt.gasUsed+tx_receipt1.gasUsed)
  
  
# def close_cvc_abnormal_and_exchange_coins(Ingrid_and_Bob_Balance, zero, value):

# Lấy phiếu bầu
def committee(transactionId,value):
  # Tạo sự kiện bình chọn
  tx_hash1=commit.functions.createVote(transactionId,value).transact({"from":Voter_1,"value":0})
  tx_receipt1=web3.eth.wait_for_transaction_receipt(tx_hash1)
  # Thành viên nộp tiền đặt cọc
  tx_hash2=commit.functions.pay().transact({"from":Voter_1,"value":value})
  tx_hash3=commit.functions.pay().transact({"from":Voter_2,"value":value})
  tx_hash4=commit.functions.pay().transact({"from":Voter_3,"value":value})
  tx_receipt2=web3.eth.wait_for_transaction_receipt(tx_hash2)
  tx_receipt3=web3.eth.wait_for_transaction_receipt(tx_hash3)
  tx_receipt4=web3.eth.wait_for_transaction_receipt(tx_hash4)
  # Vote
  tx_hash5=commit.functions.vote(Voter_1,1,transactionId).transact({"from":Voter_1,"value":0})
  tx_hash6=commit.functions.vote(Voter_2,1,transactionId).transact({"from":Voter_1,"value":0})
  tx_hash7=commit.functions.vote(Voter_3,1,transactionId).transact({"from":Voter_1,"value":0})
  tx_receipt5=web3.eth.wait_for_transaction_receipt(tx_hash5)
  tx_receipt6=web3.eth.wait_for_transaction_receipt(tx_hash6)
  tx_receipt7=web3.eth.wait_for_transaction_receipt(tx_hash7)
  # Nhận kết quả vote
  tx_hash8=commit.functions.getVoteRes(transactionId).transact({"from":Voter_1,"value":0})
  tx_receipt8=web3.eth.wait_for_transaction_receipt(tx_hash8)
  res=commit.functions.getTrue(transactionId).call()
  print("voting_result:", res)
  # trừng phạt
  # tx_hash9=commit.functions.punishment(transactionId).transact({"from":Voter_1,"value":0})
  # tx_receipt9=web3.eth.wait_for_transaction_receipt(tx_hash9)
  print("commitee cost : ",tx_receipt1.gasUsed+tx_receipt2.gasUsed+tx_receipt3.gasUsed+tx_receipt4.gasUsed+tx_receipt5.gasUsed+
            tx_receipt6.gasUsed+tx_receipt7.gasUsed+tx_receipt8.gasUsed)
  return res

# Chọn người trung gian
def chooseIntermediary(account):
  tx_hash=commit.functions.chooseIntermediary(account).transact({"from":Voter_1,"value":0})
  tx_receipt=web3.eth.wait_for_transaction_receipt(tx_hash)
  print("chooseIntermediary cost :",tx_receipt)

# Nhận giá trị f của một người
def getF(account):
  tx_hash=commit.functions.getF(account).transact({"from":Voter_1,"value":0})
  tx_receipt=web3.eth.wait_for_transaction_receipt(tx_hash)
  m=commit.functions.getf(account).call()
  print(m)
  print("getf cost :",tx_receipt)

# c
def getAllF():
  for i in range (0,9):
      account=web3.eth.accounts[i]
      Channels.functions.getF(account).transact({"from":Voter_1,"value":0})
      t=Channels.functions.getf(account).call()
      print(t)

Times = []
# Triển khai hợp đồng, lấy địa chỉ của hợp đồng, sau đó tiến hành các bước sau:：
for i in range (1):
  committee_contract_address = Deployment_committee_contract()
  commit = web3.eth.contract(committee_contract_address, abi=abi_2)
  Deployment_channel_contract()
  deploy_lc(Ingrid,Bob,0)   # Xây dựng kênh sổ cái
  update_lc(0)    # Cập nhật kênh sổ cái
  deploy_cvc(Ingrid, Bob, 0, 0)    #Xây dựng kênh ảo cross-chain
  update_cvc(0)   # Cập nhật kênh ảo cross-chain
  # close_cvc(0)    # Đóng kênh ảo cross-chain bth
  close_cvc_abnormal(committee_contract_address,1,0,0,0)   # Đóng kênh ảo cross-chain
  # close_lc(0)   # Đóng kênh sổ cái bình thường
  close_lc_pessimistic(0)   # Đóng kênh sổ cái bất thường

Times = np.array(Times) 
print(Times.mean())


















