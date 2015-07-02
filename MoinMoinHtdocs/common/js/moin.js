

var MOIN_SCRIPT_ROOT = "/ptri";

/////////////////////////////////////////////////////////////////
function processForGecko(obj, f)
{
    /* Find the Start and End Position */
    var start = obj.selectionStart;
    var end   = obj.selectionEnd;
    var text = obj.value.substr(start,end);
    text = f(text.substr(0,end-start));
    /* Remember obj is a textarea or input field */
    obj.value = obj.value.substr(0, start)
        + text
        + obj.value.substr(end, obj.value.length);
    obj.focus();
    obj.setSelectionRange(start, start + text.length);
}

function processForIE(obj,f)
{
    /* First of all, focus the object, we want to work with
       If we do not do so, it is possible, that the selection
       is not, where we expect it to be
    */
    obj.focus();

    /* Create a TextRange based on the document.selection
       This TextRanged can be used to replace the selected
       Text with the new one
    */
    var range = document.selection.createRange();

    /* If the range is not part of our Object (remember the
       textarea or input field), stop processing here
    */
    if(range.parentElement() != obj) {
        return false;
    }

    /* Save the current value. We will need this value later
       to find out, where the text has been changed
    */
    var orig = obj.value.replace(/rn/g, "n");

    /* Replace the Text */
    text = range.text =  f(range.text);

    /* Now get the new content and save it into
       a temporary variable
    */
    var actual = tmp = obj.value.replace(/rn/g, "n");

    /* Find the first occurance, where the original differs
       from the actual content. This could be the startposition
       of our text selection, but it has not to be. Think of the
       selection "ab" and replacing it with "ac". The first
       difference would be the "c", while the start position
       is the "a"
    */
    for(var diff = 0; diff < orig.length; diff++) {
        if(orig.charAt(diff) != actual.charAt(diff)) break;
    }

    /* To get the real start position, we iterate through
       the string searching for the whole replacement
       text - "abc", as long as the first difference is not
       reached. If you do not understand that logic - no
       blame to you, just copy & paste it ;)
    */
    for(var index = 0, start = 0;
        tmp.match(text)
            && (tmp = tmp.replace(text, ""))
            && index <= diff;
        index = start + text.length
    ) {
        start = actual.indexOf(text, index);
    }

}

function textProcess(obj,f)
{
    if(document.selection) {
        // Go the IE way
        processForIE(obj,f);
    } else if(obj.selectionStart) {
        // Go the Gecko way
        processForGecko(obj,f);
    } else {
        // Fallback for any other browser

    }
}

//////////////////////////////////////////////////
function get_goto_obj() {
    var obj;
    obj = document.getElementById('searchinput');
    if (!obj) {
        obj= document.getElementById('goto_panel');
    }
    return obj;
}

//////////////////////////////////////////////////
// function popup_engdic() {
//     //daum dic
//     //url = 'http://engdic.daum.net/DIC/popup_engsearch';
//     //openWindow=window.open(url,'dic','width=350,height=450,resizable=no,scrollbars=yes');

//     //naver dic
//     openWindow = window.open("http://endic.naver.com/endicsm.php",
//         "DirectSearch_Dic",
//         "width=358,height=450,resizable=yes,scrollbars=yes");
//     openWindow.focus();
// }
//////////////////////////////////////////////////
function get_script_root(href)
{
    return MOIN_SCRIPT_ROOT;
}

function set_script_root(root)
{
    MOIN_SCRIPT_ROOT = root;
}

function getPageName()
{
    var href = location.href;
    var pagename = '';
    var idx;

    //CASE of the 'goto action'
    var findstr = '?=&goto=';
    idx = href.indexOf(findstr);
    if (idx != -1) {
        pagename = href.substring(idx+findstr.length);//pagename
    }
    else {
        //CASE of the normal operation
        var cgi = get_script_root(href)
        idx = href.indexOf(cgi+'/');
        if (idx == -1) pagename = 'FrontPage';//default startpage
        else {
            //determine a end-index of pagename in a URL
            var endidx1 = href.indexOf("?");	//before query
            var endidx2 = href.indexOf("#");	//before PREVIEW
            if (endidx1 == -1 && endidx2 == -1)
                endidx = href.length;
            else if (endidx1 == -1) endidx = endidx2;
            else if (endidx2 == -1) endidx = endidx1;
            else
                endidx = (endidx1>endidx2)?endidx2:endidx1;

            //extract a pagename
            pagename = href.substring(idx+cgi.length+1, endidx);
        }
    }
    return pagename;
}

//////////////////////////////////////////////////
function wiki_edit() {
    if (typeof gui_editor_link_href !="undefined") {
        var edit_link = gui_editor_link_href.substring(0,gui_editor_link_href.length-11);
        window.location = edit_link;
    }
    else {
        wiki_action(getPageName(), "edit");
    }
}

function wiki_action(pagename, actionStr) {
    var cgi = get_script_root(location.href);
    window.location = cgi + '/' + pagename+'?action='+actionStr;
}

function wiki_page(pagename) {
    var cgi = get_script_root(location.href);
    window.location = cgi + '/' + pagename;
}


var bConverted = false;
var bLoaded = false;

//codemirror
function toggleFullscreenEditing()
{
    var editorDiv = $('.CodeMirror-scroll');
    if (!editorDiv.hasClass('fullscreen')) {
        toggleFullscreenEditing.beforeFullscreen = { height: editorDiv.height(), width: editorDiv.width() }
        editorDiv.addClass('fullscreen');
        editorDiv.height('100%');
        editorDiv.width('100%');
        editor.refresh();
    }
    else {
        editorDiv.removeClass('fullscreen');
        editorDiv.height(toggleFullscreenEditing.beforeFullscreen.height);
        editorDiv.width(toggleFullscreenEditing.beforeFullscreen.width);
        editor.refresh();
    }
}

//codemirror
function convert_editor(lang) {

    var editorObj = document.getElementById('editor-textarea');
    var text = editorObj.innerHTML;
    var theme = 'solarized';

    if (text.indexOf('#format python') >= 0) {
        lang = 'python';
    }
    else if (text.indexOf('#format sql') >= 0) {
        lang = 'sql';
    }
    else {
        lang = 'tiddlywiki';
    }

    if (editorObj && bLoaded != lang) {

        var head= document.getElementsByTagName('head')[0];
        var script = null;
        var css = null;

        if (!bLoaded) {
            //script
            script= document.createElement('script');
            script.type= 'text/javascript';
            script.src= '/moin_static195/common/codemirror-5.1/lib/codemirror.js';
            head.appendChild(script);

            //css
            css = document.createElement('link');
            css.rel = 'stylesheet';
            css.href= '/moin_static195/common/codemirror-5.1/lib/codemirror.css';
            head.appendChild(css);

            //css
            var css = document.createElement('link');
            css.rel = 'stylesheet';
            css.href= '/moin_static195/common/codemirror-5.1/theme/' + theme + '.css';
            head.appendChild(css);
        }

        //script
        script= document.createElement('script');
        script.type= 'text/javascript';
        script.src= '/moin_static195/common/codemirror-5.1/mode/'+lang+'/' + lang + '.js';
        head.appendChild(script);

        //script
        //script= document.createElement('script');
        //script.type= 'text/javascript';
        //script.src= '/moin_static195/common/js/codemirror_run.js';
        //head.appendChild(script);

        //codemirror_run(document);
        bLoaded = lang;
    }

    //editorObj.insertBefore(opt);
    //editorObj.nextSibling.appendChild(theme_sel);
    //editorObj.nextSibling.appendChild(lang_sel);
    if (typeof(CodeMirror) != 'undefined' && !bConverted) {

        var options = {
            mode: lang,
            theme: theme,
            lineNumbers:true,
            onKeyEvent: function(i, e) {
                // Hook into F11
                if ((e.keyCode == 122 || e.keyCode == 27) && e.type == 'keydown') {
                    e.stop();
                    return toggleFullscreenEditing();
                }
            },
        };
        myCodeMirror = CodeMirror.fromTextArea(editorObj, options);
        bConverted = true;
    }
    //myCodeMirror.setOption("mode", 'python');
    //myCodeMirror.setOption("theme", 'rubyblue');
}

//////////////////////////////////////////////////
function wikifinder_focus_on() {
    var obj = get_goto_obj();
    if (obj) {
        obj.style.display = '';
        obj.focus();
    }
    else {
        alert('error-goto_panelobj');
    }
}

document.onkeypress = function (e) {
    var e = null,
        isNav = true;

    if (parseInt(navigator.appVersion) >= 4) {
        if (navigator.appName == "Netscape") {
            isNav = true;
        } else {
            isNav = false;
        }
    }

    var hotkey = new Array();
    hotkey['e'] = "javascript:wiki_edit();";
    // hotkey['d'] = "javascript:popup_engdic();";
    hotkey['r'] = "javascript:wiki_page('RecentChanges');";
    hotkey['f'] = "javascript:wiki_page('FrontPage');";
    hotkey['z'] = "javascript:wikifinder_focus_on();";
    hotkey['['] = "javascript:wiki_action(getPageName(), 'RenamePage');";
    hotkey[']'] = "javascript:wiki_action(getPageName(), 'DeletePage');";
    hotkey['9'] = "javascript:wiki_action(getPageName(), 'quicklink');";
    hotkey['0'] = "javascript:wiki_action(getPageName(), 'quickunlink');";
    hotkey['a'] = "javascript:wiki_action(getPageName(), 'AttachFile');";
    hotkey['q'] = "javascript:convert_editor(null);";

    if (window.event) e = window.event;
    var srcEl = e.srcElement?e.srcElement:e.target;
    var nCode = (isNav)?e.which:e.keyCode;

    if ( (srcEl.tagName != 'INPUT') && (srcEl.tagName != 'TEXTAREA') )
    {
        var sKey = String.fromCharCode(nCode).toLowerCase();
        for (var i in hotkey) {
            if (sKey == i && hotkey[i]) {
                window.location = hotkey[i];
            }
        }
    }
    else if (srcEl.tagName == 'TEXTAREA')
    {
        // if (e.ctrlKey) {
        //     if (nCode == 32) { //ctrl + space
        //         textProcess(srcEl,function (text) { return '[['+text+']]'; });
        //         return false;
        //     }
        //     else if (nCode == 75) { //ctrl + k
        //         textProcess(srcEl,function (text) { return '--('+text+')--'; });
        //         return false;
        //     }
        //     else if (nCode == 0x31) { //ctrl + 1
        //         textProcess(srcEl,function (text) { return '= '+text+' ='; });
        //         return false;
        //     }
        //     else if (nCode == 0x32) { //ctrl + 2
        //         textProcess(srcEl,function (text) { return '== '+text+' =='; });
        //         return false;
        //     }
        //     else if (nCode == 59) {
        //         textProcess(srcEl, function (text) { return '---- ' + get_moin_datetime() + '\n\n' + text; });
        //         return false;
        //     }
        //     else if (nCode != 17) {//not ctrl key
        //     }
        // }

        // console.log(e.ctrlKey, nCode);
    }
}


function display_toggle(id) {
	var divobj = document.getElementById(id);
	if (!divobj) return;

	if (divobj.style.display == '') {
		divobj.style.display = 'none';
	}
	else {
		divobj.style.display = '';
	}
}

// // 쿠키가 있나 찾습니다
// function getCookie(name){
// 	var nameOfCookie = name + "=";
// 	var x = 0;
// 	while ( x <= document.cookie.length )
// 	{
// 		var y = (x+nameOfCookie.length);
// 		if ( document.cookie.substring( x, y ) == nameOfCookie ) {
// 			if ( (endOfCookie=document.cookie.indexOf( ";", y )) == -1 )
// 				endOfCookie = document.cookie.length;
// 			return unescape( document.cookie.substring( y, endOfCookie ) );
// 		}
// 		x = document.cookie.indexOf( " ", x ) + 1;
// 		if ( x == 0 )
// 			break;
// 	}
// 	return "";
// }

// // 쿠키를 만듭니다. 아래 closeWin() 함수에서 호출됩니다
// function setCookie( name, value, expiredays )
// {
//     var todayDate = new Date();
//     todayDate.setDate( todayDate.getDate() + expiredays );
//     document.cookie = name + "=" + escape( value ) + "; path=/; expires=" + todayDate.toGMTString() + ";"
// }


function getXmlHttpRequest() {
    var xmlhttp = null;
    if (window.XMLHttpRequest) {
        xmlhttp = new XMLHttpRequest();
    }
    else {
        xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
    }
    return xmlhttp;
}

function proc_http(url, obj, text) {

    var loading_html = '',
        xmlhttp = null;

    loading_html = '';
    if (text == null || text == '') {
        loading_html += ' Loading..';
    }
    else {
        loading_html += text;
    }

    obj.innerHTML = loading_html;
    obj.style.display = '';

    xmlhttp = getXmlHttpRequest();
    xmlhttp.open("GET",url, true);
    xmlhttp.onreadystatechange = function () {
        if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            obj.innerHTML = xmlhttp.responseText;;
        }
    }
    xmlhttp.send(null);
}

function proc_http_param_jquery(url, params, divobj, text) {
    var response = $.ajax({
        url: url,
        type: 'POST',
        cache: false,
        async: false,
        data: params
    });
    //alert(xmlhttp.responseText);
    divobj.style.display = '';
    divobj.innerHTML = response.responseText;
}

//
//http://stackoverflow.com/questions/2592092/executing-script-elements-inserted-with-innerhtml
//
// function nodeName(elem, name) {
//     return elem.nodeName && elem.nodeName.toUpperCase() ===
//               name.toUpperCase();
//   }

  function evalScript(elem) {
    var data = (elem.text || elem.textContent || elem.innerHTML || "" ),
        head = document.getElementsByTagName("head")[0] ||
                  document.documentElement,
        script = document.createElement("script");

    script.type = "text/javascript";
    try {
      // doesn't work on ie...
      script.appendChild(document.createTextNode(data));
    } catch(e) {
      // IE has funky script nodes
      script.text = data;
    }

    head.insertBefore(script, head.firstChild);
    head.removeChild(script);
  }

function stripAndExecuteScript(divobj, text) {
    var scriptss = '';
    var cleaned = text.replace(/<script[^>]*>([\s\S]*?)<\/script>/gi, function(){
        scriptss += arguments[1] + '\n';
        return '';
    });

    divobj.innerHTML = cleaned;

    if (window.execScript){
        window.execScript(scriptss);
    } else {
        var head = document.getElementsByTagName('head')[0];
        var scriptElement = document.createElement('script');
        scriptElement.setAttribute('type', 'text/javascript');
        scriptElement.innerText = scriptss;
        head.appendChild(scriptElement);
        head.removeChild(scriptElement);
    }
    return cleaned;
}

function proc_http_param(url, params, divobj, text) {
    var loading_html = '',
        xmlhttp = null;

    loading_html = ''//<img src="/moin_static193/common/loading.gif" align="absmiddle">';
    if (text == null || text == '') {
        loading_html += 'Loading..';
    }
    else {
        loading_html += text;
    }

    divobj.innerHTML = loading_html;
    divobj.style.display = '';

    xmlhttp = getXmlHttpRequest();
    xmlhttp.open("POST", url, true);

    //Send the proper header information along with the request
    xmlhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    //http.setRequestHeader("Content-length", params.length);
    //http.setRequestHeader("Connection", "close");

    xmlhttp.onreadystatechange = function() {//Call a function when the state changes.
        if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            if (!divobj) {
                alert('Result object is not valid!')
            }
            else {
                //alert(xmlhttp.responseText);
                stripAndExecuteScript(divobj, xmlhttp.responseText);
                // main section of function
            //       var scripts = ["alert('heoo');"],
            //           script,
            //           children_nodes = divobj.childNodes,
            //           child,
            //           i;

            //       for (i = 0; children_nodes[i]; i++) {
            //         child = children_nodes[i];
            //         if (nodeName(child, "script" ) &&
            //           (!child.type || child.type.toLowerCase() === "text/javascript")) {
            //               scripts.push(child);
            //           }
            //       }

            //       alert(scripts);
            //       for (i = 0; scripts[i]; i++) {
            //         script = scripts[i];
            //         if (script.parentNode) {script.parentNode.removeChild(script);}
            //         evalScript(scripts[i]);
            //       }
            // }
            }
        }
    }
    xmlhttp.send(params)
}

function proc_http_param_blank(url, params, divobj) {
    var xmlhttp = null;

    divobj.style.display = '';

    xmlhttp = getXmlHttpRequest();
    xmlhttp.open("POST", url, true);

    //Send the proper header information along with the request
    xmlhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

    xmlhttp.onreadystatechange = function() {//Call a function when the state changes.
        if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            if (!divobj) {
                alert('Result object is not valid!')
            }
            else {
                stripAndExecuteScript(divobj, xmlhttp.responseText);
            }
        }
    }
    xmlhttp.send(params)
}

function proc_http_alert(url) {
    var xmlhttp = getXmlHttpRequest();
    xmlhttp.open("GET",url, true);
    xmlhttp.onreadystatechange = function () {
        if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            alert(xmlhttp.responseText);
        }
    }
    xmlhttp.send(null);
}


// function saveAuthor(authorId, commentId) {
//     var authorObj = document.getElementById(authorId);
//     var commentObj = document.getElementById(commentId);
//     if (!authorObj) alert(authorId+" Error");
//     if (!commentObj) alert(commentId+" Error");

//     var author = authorObj.value;
//     var memo = commentObj.value;

//     if (author == '' || memo == '') {
//         alert("Don't miss your name, message!");
//         if (author == '') {
//             authorObj.focus();
//         }
//         else {
//             commentObj.focus();
//         }
//         return false;
//     }
//     if (author == 'Anonymous') {
//         authorObj.value = '';
//         authorObj.focus();
//         return false;
//     }
//     setCookie('tang_pe_kr_guestbook_author',author, 365);
//     return true;
// }

// function getAuthor(authorId) {
//     var authorObj = document.getElementById(authorId);
//     var author = getCookie('tang_pe_kr_guestbook_author');
//     if (author != '') {
//         authorObj.value = author;
//         authorObj.onfocus = null;
//     }
//     else {
//         authorObj.value = 'Anonymous';
//     }
// }

// function get_moin_datetime() {
//     var objDate = new Date();
//     var strDate = "<<DateTime("+objDate.getFullYear() + "-" + objDate.getMonth()+1 + "-" + objDate.getDate() + "T";
//     strDate += objDate.getHours() + ":" + objDate.getMinutes() + ":"+objDate.getSeconds() + "+0900)>>";
//     return strDate;
// // }

// function task_periodic_check(task_id, div_id, result) {

//     var divobj = document.getElementById(div_id);

//     if (result != null &&
//         (result.states == 'SUCCESS' || result.states == 'EXECUTED')) {
//         if (divobj == null) {
//             alert(result.result);
//         }
//         else {
//             if (divobj.nodeName === "TEXTAREA") {
//                 // console.log('textarea');
//                 divobj.value = result.result;
//                 //myCodeMirror =
//                 //이건아니다.
//                 if (typeof CodeMirror !== 'undefined')
//                     CodeMirror.fromTextArea(divobj, {mode:'mysql', theme:'rubyblue', lineNumbers:true});
//             }
//             else {
//                 console.log(divobj.nodeName);
//                 divobj.innerText = result.result;
//             }
//         }
//     }
//     else {
//         function update() {
//             var response = $.ajax({
//                 url: '/__async_task_result?action=pythonruntime&task_id=' + task_id,
//                 method: 'GET',
//                 cache: false,
//                 async: false,
//                 dataType: 'json'
//             });

//             if (response) {
//                 var json = '';
//                 try {
//                     json = JSON.parse(response.responseText);
//                 }
//                 catch(e) {
//                     alert('invalid json');
//                     console.log(response.responseText);
//                     json = '';
//                 }
//                 //try-catch cannot
//                 if (json != '') {
//                     task_periodic_check(task_id, div_id, json);
//                 }
//             }
//             else {
//                 console.log('ajax call failed?');
//             }
//         }

//         setTimeout(update, 2000);
//         return;
//     }
// }
