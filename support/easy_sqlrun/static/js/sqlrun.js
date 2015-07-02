/*
*/
//this is the raw source without the syntax highlighting.
function tabulate(id, result, show_form)
{
    periodic_check(id, result, 1, show_form);
}


// function tabulate_refresh(id, result, interval)
// {
//     periodic_check_ever(id, result, 1, interval);
// }

// function graphy(id, result, show_form)
// {
//     periodic_check(id, result, 2, show_form);
// }


/*
id - html object_id
result - json-type result
type - table/graph
*/

// function periodic_check_ever(id, result, type, interval)
// {
//     var d3obj = d3.select(id);
//     console.log('periodic_check_ever - id:' + id);

//     if (result.states == 'SUCCESS' || result.states == 'EXECUTED') {
//         // d3obj.selectAll('span').remove();

//         if (result.async) {
//             // var obj = d3obj.append('div')//.style('float','left').style('position','absolute').style('border', '1px solid')
//             //     .style('font-size','11px');
//             // var d = (new Date() - new Date(result.gen_time * 1000)) / 1000;
//             // if (d < 60) d = d + 's ago.';
//             // else if (d < 60*60) d = Math.floor(d/60) + 'm ago.';
//             // else if (d < 60*60*24) d = Math.floor(d/60/60) + 'h ago.';
//             // else if (d < 60*60*24*31) d = Math.floor(d/60/60/24) + 'days ago.';
//             // else d = Math.floor(d/60/60/24/30) + 'months ago.';
//             // obj.append('span').style('text-decoration','underline').style('text-decoration','bold').text('cached:'+d);
//             // obj.append('span').text(' ');
//             // obj.append('span').style('text-decoration','underline').text(result.task_id);
//             // if (!result.error) {
//             //     obj.append('span').text(' ');
//             //     obj.append('span').style('text-decoration','underline').text(result.elapsed);
//             //     obj.append('span').text(' ');
//             //     obj.append('span').style('text-decoration','underline').text(result.rowcnt);
//             //     obj.append('span').text(' ');
//             // }
//             //     //.html('<u>' + result.task_id + '</u> ' + result.elapsed + 's ' + result.rowcnt + ' rows.' );
//             // obj.append('span').text('(');
//             // obj.append('a').attr('href', '/__async_sqlrun_forget?action=pythonruntime&task_id=' + result.task_id)
//             //                 .attr('onclick', 'javascript:proc_http_param("/__async_sqlrun_forget?action=pythonruntime&task_id=' + result.task_id + '", "", document.getElementById("'+id.substring(1, id.length)+'"));return false;')
//             //                 .text('refresh');
//             // obj.append('span').text(')');

//             console.log('set timeout -> ' + interval);
//             setTimeout(function() {
//                 var obj_id = document.getElementById(id.substring(1, id.length));
//                 console.log(id.substring(1, id.length));
//                 proc_http_param_blank('/__async_sqlrun_refresh?action=pythonruntime&task_id=' + result.task_id, '', obj_id);
//                 /*$.ajax({
//                     url: '/__async_sqlrun_refresh?action=pythonruntime&task_id=' + task_id,
//                     method: 'GET',
//                     cache: false,
//                     async: true,
//                     success: function (resp) { document.getElementById(id.substring(1, id.length)).innerHTML = resp; }
//                     });*/
//             }, interval);
//         }

//         if (result.error) {
//             d3obj.append('font').attr('color','red').text('Failed to execute ... ' + result.error_msg);
//         }
//         else {

//             // if (type == 1)
//                 __tabulate(id, result);
//             // else {
//             //     d3obj.append('div').attr('id', result.uid + '__chart')
//             //         .style('width','100%').style('height','350px');
//             //     __graphy('#' + result.uid + '__chart', result);
//             // }
//         }
//     }
//     else {
//         //d3obj.append('span').text('..');
//         //d3obj.selectAll('#states').remove();
//         //d3obj.append('span').attr('id','states').text(' ' + result.states)
//         //    .append('a').attr('href','/__async_sqlrun_revoke?action=pythonruntime&task_id=' + result.task_id).text('[cancel]')

//         var task_id = result.task_id;
//         function update() {
//             var response = $.ajax({
//                 url: '/__moinfbp/sqlrun/_result/' + task_id,
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
//                 if (json != '') {
//                     periodic_check_ever(id, json, type, interval);
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


/*
id - html object_id
result - json-type result
type - table/graph
*/

function periodic_check(id, result, type, show_form)
{
    if (typeof d3 === 'undefined') {
        //id는 #빼고
        if (document.getElementById(id.substring(1))) {
            document.getElementById(id.substring(1)).innerHTML = '<div style="background-color:yellow; color:red;"><b>SQL수행결과를 표시할 수 없습니다.</b> 최신브라우저를 사용해주세요.</div>';
        }
        return;
    }

    var d3obj = d3.select(id);

    if (result.states == 'SUCCESS' || result.states == 'EXECUTED') {

        d3obj.selectAll('span').remove();

        if (result.error) {
            // console.log(result.error_msg);
            // console.log(show_form);
            // console.log(result.error_msg == 'Check bind variables.');
            if (result.error_msg.indexOf('Check bind variables.') != 0) {
                d3obj.append('font').attr('color','red')
                                // .style('font-size','11px')
                                // .style('font-family','Lucida Console')
                                .html('Failed to execute<br><b>' + result.error_msg + '</b><br>');
            }
            else {
                show_form = true;
                d3obj.append('span')
                            // .style('font-size','11px')
                            // .style('font-family','Lucida Console')
                            .style('font-weight', 'bold')
                            .text(result.error_msg);
            }

            if (type == 1) { //graphy는 현재 동작하지 않음;
                d3obj.append('span').text('(');
                d3obj.append('a').attr('href', '/__moinfbp/sqlrun/_forget/' + result.task_id)
                                .attr('onclick', 'javascript:proc_http("/__moinfbp/sqlrun/_forget/' + result.task_id + '", document.getElementById("'+id.substring(1, id.length)+'"));return false;')
                                .text('reload');
                d3obj.append('span').text(')');
            }

        }
        else {
            if (result.async) {
                var obj = d3obj.append('div')//.style('float','left').style('position','absolute').style('border', '1px solid')
                    .style('font-size','11px');

                var d = (new Date() - new Date(result.gen_time * 1000)) / 1000;
                if (d < 60) d = d + 's ago.';
                else if (d < 60*60) d = Math.floor(d/60) + 'm ago.';
                else if (d < 60*60*24) d = Math.floor(d/60/60) + 'h ago.';
                else if (d < 60*60*24*31) d = Math.floor(d/60/60/24) + 'days ago.';
                else d = Math.floor(d/60/60/24/30) + 'months ago.';
                obj.append('span').style('text-decoration','underline').style('text-decoration','bold').text('cached:'+d);
                if (type == 1) { //graphy는 현재 동작하지 않음;
                    obj.append('span').text('(');
                    obj.append('a').attr('href', '/__moinfbp/sqlrun/_forget/' + result.task_id)
                                    .attr('onclick', 'javascript:proc_http("/__moinfbp/sqlrun/_forget/' + result.task_id + '", document.getElementById("'+id.substring(1, id.length)+'"));return false;')
                                    .text('reload');
                    obj.append('span').text(')');
                }
                obj.append('span').text(' ');
                obj.append('span').style('text-decoration','underline').text(result.task_id);
                if (!result.error) {
                    obj.append('span').text(' ');
                    obj.append('span').style('text-decoration','underline').text(result.elapsed);
                    obj.append('span').text(' ');
                    obj.append('span').style('text-decoration','underline').text(result.rowcnt);
                    obj.append('span').text(' ');
                }
                    //.html('<u>' + result.task_id + '</u> ' + result.elapsed + 's ' + result.rowcnt + ' rows.' );
            }
        }
        //form drawing
        if (show_form) {
            var keys = [];
            for (var key in result.params) {
              if (result.params.hasOwnProperty(key)) {
                keys.push(key);
              }
            }

            if (keys.length > 0) {
                var frm = d3obj.append('form')
                                .style('font-size','11px')
                                .style('font-family','Lucida Console');
                var fry = false;
                var toy = false;
                for (var i=0; i<keys.length; i++) {
                    var prop = keys[i];
                    // alert(prop);
                    if (prop == 'yyyymmdd' || prop == 'YYYYMMDD') {

                        frm.append('span').text(prop + ':');
                        frm.append('input').attr('type','text').attr('size',15)//.attr('id',result.task_id+'_' + prop)
                            .style('background-color', 'aliceblue')
                            .attr('class','datepicker_'+result.task_id);

                        var cal_input = $('.datepicker_'+result.task_id).pickadate({
                            formatSubmit: 'yyyy mm dd',
                            format: 'yyyy-mm-dd',
                            hiddenSuffix: 'yyyymmdd'
                        });
                        var calendar = cal_input.data('pickadate');
                        var yyyymmdd = result.params[prop];
                        if (yyyymmdd) {
                            calendar.setDate(yyyymmdd.substring(0,4), yyyymmdd.substring(4,6), yyyymmdd.substring(6,8));
                        }
                    }
                    else if (prop == 'from_yyyymmdd') {
                        fry = true;
                    }
                    else if (prop == 'to_yyyymmdd') {
                        toy = true;
                    }
                    else if (prop == 'yyyymm') {

                        frm.append('span').text(prop + ':');
                        frm.append('input').attr('type','text').attr('size',15)//.attr('id',result.task_id+'_' + prop)
                            .style('background-color', 'aliceblue')
                            .attr('class','datepicker_m_'+result.task_id);

                        var cal_input = $('.datepicker_m_'+result.task_id).pickadate({
                            formatSubmit: 'yyyy mm',
                            format: 'yyyy-mm',
                            hiddenSuffix: 'yyyymm'
                        });
                        var calendar = cal_input.data('pickadate');
                        var yyyymm = result.params[prop];
                        if (yyyymm) {
                            calendar.setDate(yyyymm.substring(0,4), yyyymm.substring(4,6), 1);
                        }
                    }
                    else {
                        frm.append('span').text(prop + ':');
                        frm.append('input').attr('type','text').attr('size',25)//.attr('id',result.task_id+'_' + prop)
                            .style('background-color', 'aliceblue')
                            .attr('name',prop)
                            .attr('value',result.params[prop]);
                    }
                }

                if (fry && toy) {


                    frm.append('span').text('range:');
                    frm.append('input').attr('type','text').attr('size',15)//.attr('id',result.task_id+'_' + prop)
                        .style('background-color', 'aliceblue')
                        .attr('id','picker_from_'+result.task_id);
                    frm.append('span').text(' - ');
                    frm.append('input').attr('type','text').attr('size',15)//.attr('id',result.task_id+'_' + prop)
                        .style('background-color', 'aliceblue')
                        .attr('id','picker_to_'+result.task_id);

                    // Create an array from the date while parsing each date unit as an integer
                    function createDateArray( date ) {
                        return date.split( '-' ).map(function( value ) { return +value })
                    }

                    // When a date is selected on the "from" picker,
                    // get the date and split into an array.
                    // Then set the lower limit of the "to" picker.
                    var picker_from = $( '#picker_from_' + result.task_id ).pickadate({
                        onSelect: function() {
                            var fromDate = createDateArray( this.getDate( 'yyyy-mm-dd' ) );
                            picker_to.data( 'pickadate' ).setDateLimit( fromDate );
                        },
                        formatSubmit: 'yyyy mm dd',
                        format: 'yyyy-mm-dd',
                        hiddenSuffix: 'from_yyyymmdd'

                    });

                    // When a date is selected on the "to" picker,
                    // get the date and split into an array.
                    // Then set the upper limit of the "from" picker.
                    var picker_to = $( '#picker_to_' + result.task_id ).pickadate({
                        onSelect: function() {
                            var toDate = createDateArray( this.getDate( 'yyyy-mm-dd' ) );
                            picker_from.data( 'pickadate' ).setDateLimit( toDate, 1 );
                        },
                        formatSubmit: 'yyyy mm dd',
                        format: 'yyyy-mm-dd',
                        hiddenSuffix: 'to_yyyymmdd'
                    });

                    var calendar_from = picker_from.data('pickadate');
                    var from_yyyymmdd = result.params['from_yyyymmdd'];
                    if (from_yyyymmdd) {
                        calendar_from.setDate(from_yyyymmdd.substring(0,4), from_yyyymmdd.substring(4,6), from_yyyymmdd.substring(6,8));
                    }

                    var calendar_to = picker_to.data('pickadate');
                    var to_yyyymmdd = result.params['to_yyyymmdd'];
                    if (to_yyyymmdd) {
                        calendar_to.setDate(to_yyyymmdd.substring(0,4), to_yyyymmdd.substring(4,6), to_yyyymmdd.substring(6,8));
                    }

                }

                frm.append('input').attr('type','submit');
            }
        }

        if (result.error) {
        }
        else {

            if (type == 1)
                __tabulate(id, result);
            else {
                // // d3obj.append('div').attr('id', result.uid + '__chart')
                // //     .style('width','100%').style('height','350px');
                // // __graphy('#' + result.uid + '__chart', result);
                // __graphy_d3(id, result);
            }
        }
    }
    else {
        //d3obj.append('span').text('..');
        var message = '';
        if (result.states == 'SENT' || result.states == 'PENDING') { 
            message = result.task_id + ' 작업을 요청중입니다.(상태:' + result.states + ')'; 
        }
        else if (result.states == 'STARTED') {
            message = '요청작업(' + result.task_id + ')을 수행중입니다.';
        }
        else {
            message = result.states;
        }

        d3obj.selectAll('#states').remove();
        d3obj.append('span')
                .attr('id','states')
                .style("color","white")
                .transition()
                .duration(5000)
                .style("background-color","#ffffff").text(message)
                ;
        //    .append('a').attr('href','/__async_sqlrun_revoke?action=pythonruntime&task_id=' + result.task_id).text('[cancel]')

        var task_id = result.task_id;
        function update() {
            var response = $.ajax({
                url: '/__moinfbp/sqlrun/_result/' + task_id,
                method: 'GET',
                cache: false,
                async: false,
                dataType: 'json'
            });

            if (response) {
                var json = '';
                try {
                    json = JSON.parse(response.responseText);
                }
                catch(e) {
                    alert('invalid json');
                    console.log(response.responseText);
                    json = '';
                }
                if (json != '') {
                    periodic_check(id, json, type, show_form);
                }
            }
            else {
                console.log('ajax call failed?');
            }
        }
        setTimeout(update, 5000);
        return;
    }
}
// function __graphy_d3(id, result)
// {
//     var d3obj = d3.select(id),
//         color = d3.scale.category10(),
//         margin = {top: 30, right: 0, bottom: 60, left: 60}
//         ;

//     var width = 1400 - margin.right,
//         height = 400 - margin.top - margin.bottom;

//     var x,
//         path,
//         y = d3.scale.linear().range([height,0]);

//     //construct data
//     var data = result.rows;
//     var keys = result.columns;
//     // for (var i=0; i<result.rows.length; i++) {
//     //     var record = {};
//     //     for (var j=0; j<result.columns.length; j++) {
//     //         record[result.columns[j]] = result.rows[i][j];
//     //     }
//     //     data.push(record);
//     // }

//     //date check
//     // var date_check = false;
//     var minmax_range = [];
//     // if (keys[0] == 'YYYYMMDD') {
//     //     date_check = true;
//     // }
//     for (var i=1; i<keys.length; i++) {
//         minmax_range.push(d3.max(data, function(d) { return d[i]; }));
//         minmax_range.push(d3.min(data, function(d) { return d[i]; }));
//     }
//     // var date_formatter = d3.time.format("%Y%m%d");
//     // if (date_check) {
//     //     keys = d3.set(keys);
//     //     keys.remove("YYYYMMDD");
//     //     keys = keys.values();
//     //     data.forEach(function (d) {
//     //         console.log(d.YYYYMMDD);
//     //         d.YYYYMMDD = date_formatter.parse(d.YYYYMMDD);
//     //         console.log(d.YYYYMMDD);
//     //     });
//     // }

//     // var paths = [];
//     // if (date_check) {



//     //     x = d3.time.scale()
//     //                 .domain(d3.extent(data, function(d) { return d.YYYYMMDD; }))
//     //                 .range([0, width]);
//     //     // for (var idx=0; idx<keys.length; idx++) {
//     //     //     paths.push(d3.svg.line()//.interpolate("basis")
//     //     //                         .x(function(xd) { return x(xd.YYYYMMDD); })
//     //     //                         .y(function(yd) { console.log(idx, keys, keys[idx], yd[keys[idx]]); return y(+yd[keys[idx]]); }));
//     //     // }
//     // }
//     // else
//     {


//         x = d3.scale.ordinal()
//             .domain(data.map(function (d) { return d[0]; }))
//             .rangeRoundBands([0, width], .1);
//         // x = d3.scale.linear()//ordinal.scale()
//         //             .domain([0, data.length])
//         //             .range([0, width]);
//         // for (var i=0; i<keys.length; i++) {
//         //     paths.push(d3.svg.line()//.interpolate("basis")
//         //                         .y(function(yd) { return y(+yd[keys[i]]); }));
//         // }
//     }
//     // console.log(data);
//     // console.log(paths);
//     color.domain(keys);
//     // y.domain(d3.extent(minmax_range));
//     y.domain([0, d3.max(minmax_range)]);
//     // console.log(y.domain());


//     var svg = d3obj
//         .append("svg")
//         .attr("width", width + margin.left + margin.right)
//         .attr("height", height + margin.top + margin.bottom)
//         .style("margin-left", margin.left + "px")
//         .append("g")
//         .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
//         ;


//     var xaxis = svg.append("g")
//         .attr("class", "x axis")
//         .attr("transform", "translate(0," + height + ")")
//         .call(x.axis = d3.svg.axis().scale(x).ticks(10).orient("bottom"));



//     // var path = svg.append("g")
//     //     .selectAll("path")
//     //     .data(keys)
//     //     .enter()
//     //     .append("path")
//     //     .attr("class", "line")
//     //     .attr("d", function (d, i) {
//     //         var p;
//     //         if (date_check) {
//     //             p = d3.svg.line()//.interpolate("basis")
//     //                         .x(function(xd) { return x(xd.YYYYMMDD); })
//     //                         .y(function(yd) { return y(+yd[keys[i]]); });
//     //         }
//     //         else {
//     //             p = d3.svg.line()//.interpolate("basis")
//     //                         .x(function(xd, xi) { return x(xi); })
//     //                         .y(function(yd) { return y(+yd[keys[i]]); });
//     //         }
//     //         return p(data);
//     //     })
//     //     // .style("opacity", "0.3")
//     //     .style("stroke", function(d, i) {
//     //         return color(d);
//     //     });
//     var barEnter = svg.selectAll(".bar")
//         .data(data)
//         .enter()
//         ;

//     barEnter.append("rect")
//         .attr("class", "bar")
//         .attr("x", function(d) { console.log(d, x(d[0])); return x(d[0]); })
//         .attr("width", x.rangeBand())
//         .attr("y", function(d, i) { console.log(i, +d[1]); return y(+d[1]); })
//         .attr("height", function(d) { return height - y(+d[1]); })
//         .style("fill", color(keys[1]))
//         ;

//     var yaxis = svg.append("g")
//         .attr("class", "y axis")
//         .call(y.axis = d3.svg.axis().scale(y).ticks(6).tickFormat(d3.format("3s")).orient("left"))
//         .append("text")
//         .attr("transform", "rotate(-90)")
//         .attr("y", 6)
//         .attr("dy", ".71em")
//         .style("text-anchor", "end")
//         .text(keys[1]);
// }
function __tabulate(id, result)
{
    var d3obj = d3.select(id);
    var table = d3obj.append('table'),
        thead = table.append('thead'),
        tbody = table.append('tbody');

    thead.append('tr')
        .selectAll('th')
        .data(result.columns)
        .enter()
        .append('th')
        //.attr("onclick", function (d, i) { return "__sortable_tabulate('" + d + "');";})
        .text(function(col) { return col; });

    // create a row for each object in the data
    var rows = tbody.selectAll("tr")
        .data(result.rows)
        .enter()
        .append("tr");
        //.sort(function (a, b) { return a == null || b == null ? 0 : stringCompare(a[key_index], b[key_index]); });

    // filter
    var re_tr = /^z[a-z]{3}s[a-z0-9]{8}_tr[0-9]{2}$/i;
    var re_dbio = /^z[a-z_]+[sfudi][0-9]{4}$/i;
    var re_svc = /^(z)?[a-z]{3}[smb][a-z0-9]{8}(t[0-9]{2})?(\.c|\.pc|\.xml)?$/i;

    var cells = rows.selectAll("td")
        .data(function(row) {
            return row;
        })
        .enter()
        .append('td')
        .on("mouseover", function(){d3.select(this).style("background-color", "aliceblue")})
        .on("mouseout", function(){d3.select(this).style("background-color", "white")})
        .html(function (d) { if (re_tr.test(d) || re_dbio.test(d) || re_svc.test(d)) { return '<a href="/'+d+'">'+d+'</a>'; }
                            else { return d; }
              }
        );
}

// function __graphy(id, result)
// {
//     var options = {};
//     var placeholder = $(id);

//     var date_check = -1;
//     for (var i=0; i<result.columns.length; i++) {
//         if (result.columns[i] == 'YYYYMMDD') {
//             date_check = i;
//             break;
//         }
//     }

//     //
//     var data = [];
//     if (date_check >= 0) {
//         date_data = []
//         result.rows.forEach(function(d) {
//             date_data.push(d3.time.format("%Y%m%d").parse(d[date_check]));
//             console.log(d[date_check]);
//             console.log(d3.time.format("%Y%m%d").parse(d[date_check]));
//         });

//         for (var i=0; i<result.columns.length; i++) {
//             if (i == date_check) {}
//             else {
//                 var series = [];
//                 for (var j=0; j<result.rows.length; j++) {
//                   series.push([date_data[j],parseInt(result.rows[j][i])]);
//                   // console.log([date_data[i],parseInt(result.rows[j][i])]);
//                 }
//                 data.push({'data':series, 'label':result.columns[i]});
//             }
//         }

//         options = {
//             grid: { show: true },
//             lines: { show: true },
//             points: { show: true },
//             xaxis: { mode: "time" }
//         };
//     }
//     else {
//         for (var i=0; i<result.columns.length; i++) {
//             var series = [];
//             for (var j=0; j<result.rows.length; j++) {
//               series.push([j,parseInt(result.rows[j][i])]);
//               // console.log([j,parseInt(result.rows[j][i])]);
//             }
//             data.push({'data':series, 'label':result.columns[i]})
//         }

//         options = {
//             grid: { show: true },
//             lines: { show: true },
//             points: { show: true },
//             xaxis: { tickDecimals: 0, tickSize: 1 }
//         };
//     }
//     // and plot all we got
//     $.plot(placeholder, data, options);
// }

// function __graphy2(placeholder, dataurl) {
//     var options = {
//         grid: { show: false },
//         lines: { show: true },
//         points: { show: true },
//         xaxis: { tickDecimals: 0, tickSize: 1 }
//     };

//     var data = [];
//     $.plot(placeholder, data, options);

//     // then fetch the data with jQuery
//     function onDataReceived(json_rst) {

//         // var date_check = -1;
//         // for (var i=0; i<json_rst.columns.length; i++) {
//         //     if (json_rst.columns[i] == 'YYYYMMDD') {
//         //         date_check = i;
//         //         break;
//         //     }
//         // }

//         // if (date_check >= 0) {
//         //     json_rst.rows.forEach(function(d) {
//         //         d[date_check] = d3.time.format("%Y%m%d").parse(d[date_check]);
//         //     });
//         //     d3.time.format("%Y%m%d").parse();
//         // }

//         for (var i=0; i<json_rst.columns.length; i++) {
//             var series = [];
//             for (var j=0; j<json_rst.rows.length; j++) {
//               series.push([j,parseInt(json_rst.rows[j][i])]);
//               console.log([j,json_rst.rows[j][i]]);
//             }
//             // data.push({'data':series, 'label':json_rst.columns[i]})
//         }
//         //alert(data);
//         // and plot all we got
//         $.plot(placeholder, data, {});
//         //[[1999, 4.4], [2000, 3.7], [2001, 0.8], [2002, 1.6], [2003, 2.5], [2004, 3.6], [2005, 2.9], [2006, 2.8], [2007, 2.0], [2008, 1.1]]}], {});
//      }

//     $.ajax({
//         url: dataurl,
//         method: 'GET',
//         dataType: 'json',
//         success: onDataReceived
//     });
// }
