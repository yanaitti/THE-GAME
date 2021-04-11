var timeout = 1000;
var timer = '';

$(function() {
  var gId = '';
  var cId = '';
  $('#entry').show();

  $('#clickCopy').click(function(){
    var text = $('#uriWgId').val();
    var clipboard = $('<textarea></textarea>');
    clipboard.text(text);
    $('body').append(clipboard);
    clipboard.select();
    document.execCommand('copy');
    clipboard.remove();
  });

  // Create Game
  $('#createGame').click(function() {
    $('#message').empty();
    $.ajax('/create' + '/' + $('#cName_inp').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
      $('#gId').text(data);
      $('#cId').text(data);
      $('#cName').text($('#cName_inp').val());
      $('#gStatus').text('waiting');
      $('#uriWgId').val(location.href + data + '/join');
      gId = data;
      cId = data;
      $('#sec1').show();
      timer = setTimeout(status_check(gId, cId), timeout)
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // Join Game
  $('#joinGame').click(function() {
    $('#message').empty();
    $.ajax('/' + $('#gId_inp').val() + '/join/' + $('#cName_inp').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
      _tmp = data.split(' ,');
      $('#cId').text(_tmp[0]);
      $('#cName').text(_tmp[1]);
      $('#gStatus').text(_tmp[2]);
      gId = $('#gId_inp').val();
      cId = _tmp[0];
      timer = setTimeout(status_check(gId, cId), timeout)
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // Start Game
  $('#startGame').click(function() {
    $('#message').empty();
    $.getJSON('/' + gId + '/start/' + $('input:checkbox[name="rule_type"]:checked').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // Put your card
  $('#putCard').click(function() {
    $('#message').empty();
    // put your card
    $.ajax('/' + gId + '/' + cId + '/set/' + $('input[name="area"]:checked').val() + '/' + $('#cardNum_inp').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
      $('#message').text(data);
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
    $('#cardNum_inp').val('')
  });

  // Next player
  $('#nextPlayer').click(function() {
    $('#message').empty();
    $.ajax('/' + gId + '/next',
      {
        type: 'get',
      }
    )
    .done(function(data) {
      // console.log(data)
      $('#message').text('次の人に移動しました');
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });
});

var status_check = function(gId, cId){
  setTimeout(function(){
    $('#message').empty();
    // all status
    $.getJSON('/' + gId + '/status',
      {
        type: 'get',
      }
    )
    .done(function(data) {
      console.log(data)
      $('#gStatus').text(data.status);
      playerPos = 0;

      // Applying List
      $('#applyingList').empty();
      for(var pIdx in data.players){
        // console.log(data.players[pIdx])
        $('#applyingList').append(data.players[pIdx].nickname + '(' + data.players[pIdx].playerid + ')' + ',');
        if(cId == data.players[pIdx].playerid){
          playerPos = pIdx;
        }
      }

      if(data.status == 'started'){
        $('#entry').hide()
        $('#sec2').show()
        // route List
        $('#routeList').empty();
        for(var rIdx in data.routelist){
          if(data.routelist[rIdx].playerid == data.routelist[data.routeidx].playerid){
            $('#routeList').append('<b>&gt;' + data.routelist[rIdx].nickname + '</b><br/>');
          }else{
            $('#routeList').append(data.routelist[rIdx].nickname + '<br/>');
          }
        }

        // game cards
        $('#gameCards0').text(data.hightolow[0])
        $('#gameCards1').text(data.hightolow[1]);
        $('#gameCards2').text(data.lowtohigh[0]);
        $('#gameCards3').text(data.lowtohigh[1]);
        // $('#gameCards0').empty();
        // $('#gameCards1').empty();
        // $('#gameCards2').empty();
        // $('#gameCards3').empty();
        // for(var i in data.hightolow[0].toString().split(',')){
        //   $('<li id="gameCards0"><font id="gameCards0">' + data.hightolow[0][i] + '</font></li>').appendTo($('#gameCards0'));
        // }
        // for(var i in data.hightolow[1].toString().split(',')){
        //   $('<li id="gameCards1">1</li>').appendTo($('#gameCards1'));
        // }
        // for(var i in data.lowtohigh[0].toString().split(',')){
        //   $('<li id="gameCards2">1</li>').appendTo($('#gameCards2'));
        // }
        // for(var i in data.lowtohigh[1].toString().split(',')){
        //   $('<li id="gameCards3">1</li>').appendTo($('#gameCards3'));
        // }

        // hold cards
        $('#holdCards').text(data.players[playerPos].holdcards.join(','))
        // submit cards
        $('#submitCards').text(data.submit.join(','))

        // checking turn
        if(data.routelist[data.routeidx].playerid == cId){
          $('#yTurn').text('your turn')
          $('#sec3').show();
          if(data.submit.length >= 2){
            $('#nextPlayer').prop('disabled', false);
          }else{
            $('#nextPlayer').prop('disabled', true);
          }
        }else{
          $('#yTurn').text('not your turn')
          $('#sec3').css('display', 'none');
        }
      }
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
    timer = setTimeout(status_check(gId, cId), timeout)
  }, timeout);
}
