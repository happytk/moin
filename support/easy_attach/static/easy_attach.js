jQuery.fn.extend({
    insertAtCaret: function(myValue) {
        return this.each(function(i) {
            if (document.selection) {
                this.focus();
                var sel = document.selection.createRange();
                sel.text = myValue;
                this.focus();
            }
            else if (this.selectionStart || this.selectionStart == '0') {
                var startPos = this.selectionStart;
                var endPos = this.selectionEnd;
                var scrollTop = this.scrollTop;
                this.value = this.value.substring(0, startPos) + myValue + this.value.substring(endPos, this.value.length);
                this.focus();
                this.selectionStart = startPos + myValue.length;
                this.selectionEnd = startPos + myValue.length;
                this.scrollTop = scrollTop;
            }
            else {
                this.value += myValue;
                this.focus();
            }
        })
    }
})


function insert_textarea(txt) {
    if (txt) {
        $('#editor-textarea').insertAtCaret(txt);
        $('#editor-textarea').focus();
    }
}

function handle_hover(e) {
    e.originalEvent.stopPropagation();
    e.originalEvent.preventDefault();
    e.target.className = (e.type == 'dragleave' || e.type == 'drop') ? '' : 'hover';
}

// function sse() {
//     var source = new EventSource('/__attach/stream');
//     source.onmessage = function(e) {
//         if (e.data == '')
//             return;
//         var data = $.parseJSON(e.data);
//         var upload_message = data['src']; //'Image uploaded by ' + data['ip_addr'];
//         var image = $('<img>', {class: 'attachment', alt: upload_message, src: '?action=AttachFile&do=get&target='+data['src']});
//         var container = $('<div>').hide();
//         container.append($('<ul>').append($('<li>', {html: '<span class="att_info">(NOW)</span><span style="background-color:yellow;">{{attachment:' + upload_message + '}}</span>'}).append(image)));
//         //container.append(image);
//         $('#images').prepend(container);
//         image.load(function(){
//             container.show('blind', {}, 1000);
//         });
//     };
// }

function file_select_handler(to_upload, path, direct) {
    var progressbar_container = $('#progressbar');        
    var progressbar = $('<div>');
    var progressbar_label = $('<div>', {class:'progress-label'});
    progressbar.append(progressbar_label);
    progressbar_container.append(progressbar);

    var status = $('#status');
    var xhr = new XMLHttpRequest();
    xhr.upload.addEventListener('loadstart', function(e1){
        //status.text('uploading...');
        progressbar.progressbar({
                                    max: 100,
                                    value: false,
                                    change: function() {
                                        var v = progressbar.progressbar('value');
                                        if (v) {
                                            progressbar_label.text(v + '%'); 
                                        }
                                    },
                                    complete: function() { /*progressbar_label.text('Complete!');*/ },
                                });
    });
    xhr.upload.addEventListener('progress', function(e1){
        if (progressbar.progressbar('option', 'max') == 0)
            progressbar.progressbar('option', 'max', 100);
        progressbar.progressbar('value', parseInt(e1.loaded/e1.total*100));
    });
    xhr.onreadystatechange = function(e1) {

        var text;
        var ext;
        var uploaded_filename;
        var attachment_text;
        var container;
        var mediatag;
        var html;
        var mediatyp;

        // console.log('hello', this.readyState, this.status);

        if (this.readyState == 4)  {
            if (this.status == 200) {
                text = this.responseText;//''; //upload complete: ';// + this.responseText;
                if (text.indexOf('success/') == 0) {
                    text = text.substring(8, text.length);
                    ext = text.substring(text.length-4, text.length);
                    // upload_message = text; //data['src']; //'Image uploaded by ' + data['ip_addr'];

                    uploaded_filename = text;

                    if (ext == '.jpg' || ext == 'jpeg' || ext == '.gif' || ext == '.png') {
                        mediatyp = 'image';
                        mediatag = $('<img>', {'class': 'attachment', 'alt': uploaded_filename, 'src': '?action=AttachFile&do=get&target='+uploaded_filename});
                    }
                    else if (ext == '.mp3') {
                        mediatyp = 'audio';
                        mediatag = $('<audio>', {'src': '?action=AttachFile&do=get&target='+uploaded_filename});
                    }
                    else if (ext == '.mp4') {
                        mediatyp = 'video';
                        mediatag = $('<video>', {'src': '?action=AttachFile&do=get&target='+uploaded_filename});
                    }
                    else {
                        mediatyp = '';
                        mediatag = $('<span>');
                    }

                    if (mediatyp != '') {
                        attachment_text = '{{attachment:' + uploaded_filename + '}}';
                    }
                    else {
                        attachment_text = '[[attachment:' + uploaded_filename + ']]';
                    }

                    //이미지표시 container만들기
                    html = {html: '<span class="att_info">(NOW)</span><span style="background-color:yellow;">'+ attachment_text + '</span>'};

                    container = $('<li>', html).hide();
                    container.append(mediatag);

                    //이미지모음 영역에 신규 container를 추가해준다.
                    $('#att_list').prepend(container);
                    if (mediatyp == 'image') {
                        mediatag.load(function(){
                            container.show('blind', {}, 1000);
                        });
                    }
                    else {
                        container.show();
                    }

                    //편집모드에서 첨부파일선택 영역을 초기화해준다 (reload시에 데이타를 새로 가져올 수 있도록)
                    //신규데이타를 넣어주는것이 더 좋지만 select2에서 기존 데이타(from ajax)에 새로 추가하는 방법을 아직 잘 모르므로
                    $('.attachment_select').val(3620194).trigger('change');
                    
                    //상태표시 update
                    progressbar_label.text('SUCCESS! ' + to_upload.name + ' -> ' + attachment_text);
                } else { /* case of error */
                    progressbar_label.text(text);
                }
            }
            else {
                // text = '<font color="red"><b>실패!: code ' + this.status + '</b></font>';
                // status.html(text);
                progressbar_label.text('FAIL! ' + to_upload.name + '(code:' + this.status + ')');
            }
            // progressbar.progressbar('destroy');
        }
        else {
            progressbar_label.text('FAIL! ' + to_upload.name + '(code:' + this.readyState + ')');
        }
    };
    xhr.open('POST', '/__moinfbp/easy_attach/post?path=' + path + '&filename=' + to_upload.name + '&direct=' + direct, true);
    xhr.send(to_upload);
};


function formatRepo (repo) {
    if (repo.loading) return repo.text;
    return '<div>' + repo.text + '</div>';
}

function formatRepoSelection (repo) {
    return repo.full_name || repo.text;
}


function attformatRepo (repo) {
if (repo.loading) return repo.text;
    // console.log(repo);
    if (repo.ext == '.jpg' || repo.ext == '.png' || repo.ext == '.jpg') {
        return $('<div><img src="'+ repo.src + '" style="max-width:200px; max-height:200px;"><br/>' + repo.fmtime + '(' + repo.fsize + 'k)</div>');
        // return $('<div><img src="'+ repo.src + '" style="max-width:200px; max-height:200px;"><br/>'+repo.file+'<br/>' + repo.fmtime + '(' + repo.fsize + 'k)</div>');
    }
    else {
        return $('<div>'+repo.file+'<br/>' + repo.fmtime + '(' + repo.fsize + 'k)</div>');
    }
}

function attsformatRepo (repo) {
if (repo.loading) return repo.text;
    // console.log(repo);
    if (repo.ext == '.jpg' || repo.ext == '.png' || repo.ext == '.jpg') {
        return $('<div><img src="'+ repo.src + '" style="max-width:200px; max-height:200px;"><b>' + repo.pagename + '</b><br/>' + repo.fmtime + '(' + repo.fsize + 'k)</div>');
        // return $('<div><img src="'+ repo.src + '" style="max-width:200px; max-height:200px;"><br/>'+repo.file+'<br/>' + repo.fmtime + '(' + repo.fsize + 'k)</div>');
    }
    else {
        return $('<div>'+repo.file+'<br/><b>' + repo.pagename + '</b><br/>' + repo.fmtime + '(' + repo.fsize + 'k)</div>');
    }
}
