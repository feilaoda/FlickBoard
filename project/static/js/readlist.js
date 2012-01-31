function yhdtestreadlist() {
    alert('书签已经安装.')
}
function progress_waiting(id) {
    var oldRow = document.getElementById('rlistView' + id);
    var progressDiv = document.createElement('div');
    progressDiv.setAttribute('id', 'rlistView' + id);
    progressDiv.setAttribute('class', 'rmlCellAjax');
    progressDiv.setAttribute('style', 'height: ' + oldRow.clientHeight + 'px;');
    var spinner = document.createElement('img');
    spinner.setAttribute('src', '/static/image/loading.gif');
    spinner.setAttribute('style', 'margin-top: ' + (Math.round(oldRow.clientHeight / 2) - 16) + 'px;');
    progressDiv.appendChild(spinner);
    oldRow.parentNode.replaceChild(progressDiv, oldRow)
}

function html_hide(id) {
    document.getElementById(id).style.display = 'none'
}

function html_show(id) {
    document.getElementById(id).style.display = 'inline-block'
}

function ajax_list(action,offset)
{
    $.get("/readlist/api/"+action,
        {offset:offset, limit:50},
        function(data){
            var html_str=data['html'];
            var count=data['count'];
            if(offset==0){
                $('#readListBody').html(html_str);
            }
            else{
            $('#readListBody').append(html_str);
            }
        },
        "json");
}

function list_unread(offset)
{
    if(offset == null){offset=0;}
    ajax_list('list_unread', offset);
}
function list_starred(offset)
{
    if(offset == null){offset=0;}
    $.get("/readlist/api/list_starred",
        {offset:offset, limit:50},
        function(data){
            $('#readListBody').html(data);
        },
        "html");
}
function list_private(offset)
{
    if(offset == null){offset=0;}
    $.get("/readlist/api/list_private",
        {offset:offset, limit:50},
        function(data){
            $('#readListBody').html(data);
        },
        "html");
}
function list_archived(offset)
{
    if(offset == null){offset=0;}
    $.get("/readlist/api/list_archived",
        {offset:offset, limit:50},
        function(data){
            $('#readListBody').html(data);
        },
        "html");
}


function ajax_action(action, topicid, callback)
{
   
  $.ajax({url: "/readlist/api/"+action,
         type: "POST",
         data: "topic_id="+topicid,
        dataType: "json",
        success: function (json)
        {
            if(json.result == 'ok')
            {
                callback();
            }
            else if( json.result == 'redirect' )
            {
                $(location).attr('href',json.url);
            }
        },
    });
  
}


function ajax_post(action, topicid)
{
  $.ajax({url: "/readlist/api/"+action,
         type: "POST",
         data: "topic_id="+topicid,
        dataType: "json",
        success: function (json)
        {
            if(json.result == 'ok')
            {
                $('#rlistView'+topicid).remove();
            }
            else if( json.result == 'redirect' )
            {
                $(location).attr('href',json.url);
            }
        },
    });
}



function liked_it(topicid) {
        var topicid = $(this).attr("id").substring(5);
        
        $("#loveImg"+topicid).attr("src", "/static/image/small_loading.gif");
        
        
        if($(this).attr("favorite") == "true") {
            
            ajax_doaction('do/unlike', topicid, function(){
                $("#topic"+topicid).attr("favorite", "false");
                $("#loveImg"+topicid).attr("src", "/static/image/unliked.png");
            });
        }
        else {
            ajax_doaction('do/like', topicid, function(){
                $("#topic"+topicid).attr("favorite", "true");
                $("#loveImg"+topicid).attr("src", "/static/image/liked.png");
            });
            
        }
        return false;
}

function public_it() {
        var topicid = $(this).attr("id").substring(6);
        
        $("#publicImg"+topicid).show();
        
        if($(this).attr("public") == "true") {
            $("#isPublic"+topicid).hide();
            ajax_doaction('do/private', topicid,  function(){
                $("#public"+topicid).attr("public", "false");
                $("#isPrivate"+topicid).show();
                $("#publicImg"+topicid).hide();
            });
        }
        else {
            $("#isPrivate"+topicid).hide();
            ajax_doaction('do/public', topicid,  function(){
                $("#public"+topicid).attr("public", "true");
                $("#isPublic"+topicid).show();
                $("#publicImg"+topicid).hide();
            });
            
        }
        return false;
}


function star_topic(topicid) {
        var node = $("#starImg"+topicid);
        node.attr("src", "/static/image/small_loading.gif");
        if(node.attr("favorite") === "true") {
            ajax_action('unstar', topicid, function(){
                node.attr("favorite", "false");
                node.attr("src", "/static/image/unstarred.png");
            });
        }
        else {
            ajax_action('star', topicid, function(){
                node.attr("favorite", "true");
                node.attr("src", "/static/image/starred.png");
            });
            
        }
        return false;
}

function delete_topic(topicid) {
if (!confirm("您是否确认要删除该收藏?")) return false
progress_waiting(topicid);
ajax_post('delete', topicid)
}

function archive_topic(topicid) {
progress_waiting(topicid);
ajax_post('archive', topicid)
}
function unarchive_topic(topicid) {
progress_waiting(topicid);
ajax_post('unarchive', topicid)
}


$(document).ready(function()
{
    var d=document,
    url=d.URL;
    var params=url.split("#!");
    if(params.length>=2)
    {
        api_url=params[1];
        if(api_url=="/unread"){list_unread();}
        else if(api_url == "/starred"){list_starred(0);}
        else if(api_url=="/archived"){list_archived(0);}
        else{list_unread(0);}
        
    }
    else
    {
        list_unread(0);
    }
});

function list_loadmore(offset)
{
    var d=document,
    url=d.URL;
    var params=url.split("#!");
    if(params.length>=2)
    {
        api_url=params[1];
        var func = list_unread
        if(api_url=="/unread"){func = list_unread;}
        else if(api_url == "/starred"){func = list_starred;}
        else if(api_url=="/archived"){func = list_archived;}
        
        func(0);
        
    }
    else
    {
        list_unread(0);
    }
}
