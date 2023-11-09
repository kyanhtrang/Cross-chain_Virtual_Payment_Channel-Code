// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;
contract committee{
    struct committeeman{
        address payable committeemanAddress;
        uint vote_res;
    }
    struct committeeNumber{
       uint vote_count;
       uint f; 
       uint intermediary_count;
    }
    address committeeNumberAddress;
    mapping(address=>committeeNumber) committeemap;

    struct voteEvent{
        uint transactionId;
        uint vote_true;
        uint vote_false;
        uint vote_res;
        uint committeemanAmount;
        uint cash;
        mapping (uint => committeeman) map;
    }
    // Chuyển tiền đến địa chỉ hợp đồng
    function pay() payable public{          
    }
    // Nhận số dư địa chỉ hợp đồng
    function getBalance() view public returns(uint){
        return address(this).balance;
    }
    uint voteAmount;
    mapping(uint=>voteEvent) votemap;
    // Chọn người trung gian
    function chooseIntermediary(address intermediaryAddress) public{
        committeeNumber storage _committeeNumber = committeemap[intermediaryAddress];
        _committeeNumber.intermediary_count++;
    }
    // Lấy giá trị f của người được chỉ định
    function getF(address addr) public returns(uint){
        committeeNumber storage _committeeNumber = committeemap[addr];
        _committeeNumber.f=_committeeNumber.vote_count/_committeeNumber.intermediary_count;
        return _committeeNumber.f;
    }
    function getf(address addr) view public returns(uint){
        committeeNumber storage _committeeNumber = committeemap[addr];
        return _committeeNumber.f;
    }
    // Tạo cuộc thăm dò
    function createVote(uint _transactionId,uint _cash) public{
        voteAmount = _transactionId;
        voteEvent storage n = votemap[voteAmount];
        n.transactionId = _transactionId;
        n.vote_true = 0;
        n.vote_false = 0;
        n.committeemanAmount = 0;
        n.cash=_cash;
    }
    // bỏ phiếu
    function vote(address payable _committeemanAddress, uint vote_res,uint _transactionId) public{
        voteEvent storage _voteEvent = votemap[_transactionId];
        committeeNumber storage _committeeNumber = committeemap[_committeemanAddress];
        _committeeNumber.vote_count=_committeeNumber.vote_count+1;
        if(vote_res == 1){
            _voteEvent.vote_true++;
        }
        else if(vote_res == 0){
            _voteEvent.vote_false++;
        }
        _voteEvent.committeemanAmount++;
        _voteEvent.map[_voteEvent.committeemanAmount] = committeeman(_committeemanAddress,vote_res);
    }
    // Trả về kết quả bình chọn
    function getTrue(uint _transactionId) view public returns(uint){
        voteEvent storage _voteEvent = votemap[_transactionId];
        return _voteEvent.transactionId;
    }
    // Lấy kết quả biểu quyết, vì một giá trị không thể trả về nên dùng hàm trên để trả về giá trị
    function getVoteRes(uint _transactionId) public {
        voteEvent storage _voteEvent = votemap[_transactionId];
        if(_voteEvent.vote_true>_voteEvent.vote_false){
            _voteEvent.vote_res=1;
        }
        else{
            _voteEvent.vote_res=0;
        }
    }
    // Hình phạt và số tiền phân phối
    function punishment(uint _transactionId) public {
        uint amount;
        uint each;
        voteEvent storage _voteEvent = votemap[_transactionId];
        amount = _voteEvent.committeemanAmount * _voteEvent.cash;
        if(_voteEvent.vote_res == 1){
            each = amount/_voteEvent.vote_true;
            for(uint i=1;i<=_voteEvent.committeemanAmount;i++){
                if(_voteEvent.map[i].vote_res == 1){
                    _voteEvent.map[i].committeemanAddress.transfer(each);
                    // addr.transfer(450000000000000000);
                }
            }
        }
        else{
            each = amount/_voteEvent.vote_false;
            for(uint i=1;i<=_voteEvent.committeemanAmount;i++){
                if(_voteEvent.map[i].vote_res == 0){
                    _voteEvent.map[i].committeemanAddress.transfer(each);
                }
            }
        }
    }
}
