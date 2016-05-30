/**
 * Created by riot on 02.05.16.
 * Most of this is adapted from examples around d3 on the web.
 */

var datatype = 'size';
var chartwidth = 800;

var d3_lmcolors = [
    "#fc941f", "#b9d635", "#4bbb87", "#179961", "#7c9a61",
    "#c6c6c6", "#919191", "#ebebeb"
];


function LMColor() {
    return d3.scale.ordinal().range(d3_lmcolors);
}

function buildTreeChart() {

    var w = chartwidth - 80,
        h = 800 - 180,
        x = d3.scale.linear().range([0, w]),
        y = d3.scale.linear().range([0, h]),
        color = LMColor(),
        root,
        node;

    var treemap = d3.layout.treemap()
        .round(false)
        .size([w, h])
        .sticky(true)
        .value(function (d) {
            return d.size;
        });

    var svg = d3.select("#TreeChart").append("div")
        .attr("class", "chart")
        .style("width", w + "px")
        .style("height", h + "px")
        .append("svg:svg")
        .attr("width", w)
        .attr("height", h)
        .append("svg:g")
        .attr("transform", "translate(.5,.5)");

    const DemoTreeData = {
        "name": "",
        "children": [
            {
                "name": "Animals",
                "color": "#fc941f",
                "children": [
                    {"name": "Birds", "size": 3938},
                    {"name": "Apes", "size": 3812},
                    {"name": "Sheep", "size": 6714},
                    {"name": "Mules", "size": 743}
                ]
            },
            {
                "name": "Minerals",
                "color": "#4bbb87",
                "children": [
                    {"name": "Iron", "size": 17010},
                    {"name": "Aluminium", "size": 5842},
                    {"name": "Titanium", "size": 1041},
                    {"name": "Gold", "size": 5176}
                ]
            },
            {
                "name": "Crops",
                "color": "#b9d635",
                "children": [
                    {"name": "Salad", "size": 721},
                    {"name": "Carrots", "size": 4294},
                    {"name": "Peas", "size": 9800},
                    {"name": "Cabbage", "size": 1314},
                    {"name": "Radish", "size": 2220}
                ]
            }
        ]
    };

    d3.json("", function (data) {
        node = root = DemoTreeData;

        var nodes = treemap.nodes(root)
            .filter(function (d) {
                return !d.children;
            });

        var cell = svg.selectAll("g")
            .data(nodes)
            .enter().append("svg:g")
            .attr("class", "cell")
            .attr("transform", function (d) {
                return "translate(" + d.x + "," + d.y + ")";
            })
            .on("click", function (d) {
                return zoom(node == d.parent ? root : d.parent);
            });

        cell.append("svg:rect")
            .attr("width", function (d) {
                return d.dx - 1;
            })
            .attr("height", function (d) {
                return d.dy - 1;
            })
            .style("fill", function (d) {
                console.log("The colorbook says: ", d.parent.color);
                return color(d.parent.color);
            });

        cell.append("svg:text")
            .attr("x", function (d) {
                return d.dx / 2;
            })
            .attr("y", function (d) {
                return d.dy / 2;
            })
            .attr("dy", ".35em")
            .attr("text-anchor", "middle")
            .text(function (d) {
                return d.name;
            })
            .style("opacity", function (d) {
                d.w = this.getComputedTextLength();
                return d.dx > d.w ? 1 : 0;
            });

        d3.select(window).on("click", function () {
            zoom(root);
        });

        d3.select("select").on("change", function () {
            treemap.value(this.value == "size" ? size : count).nodes(root);
            zoom(node);
        });
    });

    function size(d) {
        return d.size;
    }

    function count(d) {
        return 1;
    }

    function zoom(d) {
        var kx = w / d.dx, ky = h / d.dy;
        x.domain([d.x, d.x + d.dx]);
        y.domain([d.y, d.y + d.dy]);

        var t = svg.selectAll("g.cell").transition()
            .duration(d3.event.altKey ? 7500 : 750)
            .attr("transform", function (d) {
                return "translate(" + x(d.x) + "," + y(d.y) + ")";
            });

        t.select("rect")
            .attr("width", function (d) {
                return kx * d.dx - 1;
            })
            .attr("height", function (d) {
                return ky * d.dy - 1;
            });

        t.select("text")
            .attr("x", function (d) {
                return kx * d.dx / 2;
            })
            .attr("y", function (d) {
                return ky * d.dy / 2;
            })
            .style("opacity", function (d) {
                return kx * d.dx > d.w ? 1 : 0;
            });

        node = d;
        d3.event.stopPropagation();
    }
}

function buildPieChart() {
    var demodata = [
        {label: 'On The Lease', value: 0.3},
        {label: 'Off The Lease', value: 0.35},
        {label: 'Pure Contract Farming', value: 0.1},
        {label: 'Both', value: 0.15},
        {label: 'None', value: 0.1}
    ];

    var w = chartwidth / 2,                        //width
        h = 500,                            //height
        r = 180;                            //radius
    color = LMColor();     //builtin range of colors

    $("#PieChart").empty();

    d3.json("", function (data) {
        var data = demodata;

        var vis = d3.select("#PieChart")
            .append("svg:svg")              //create the SVG element inside the <body>
            .data([data])                   //associate our data with the document
            .attr("width", w)           //set the width and height of our visualization (these will be attributes of the <svg> tag
            .attr("height", h)
            .append("svg:g")                //make a group to hold our pie chart
            .attr("transform", "translate(" + w / 2 + "," + h / 2 + ")");    //move the center of the pie chart from 0, 0 to radius, radius

        var arc = d3.svg.arc()              //this will create <path> elements for us using arc data
            .outerRadius(r);

        var pie = d3.layout.pie()           //this will create arc data for us given a list of values
            .value(function (d) {
                return d.value;
            });    //we must tell it out to access the value of each element in our data array

        var arcs = vis.selectAll("g.slice")     //this selects all <g> elements with class slice (there aren't any yet)
            .data(pie)                          //associate the generated pie data (an array of arcs, each having startAngle, endAngle and value properties)
            .enter()                            //this will create <g> elements for every "extra" data element that should be associated with a selection. The result is creating a <g> for every object in the data array
            .append("svg:g")                //create a group to hold each slice (we will have a <path> and a <text> element associated with each slice)
            .attr("class", "slice");    //allow us to style things in the slices (like text)

        arcs.append("svg:path")
            .attr("fill", function (d, i) {
                return color(i);
            }) //set the color for each slice to be chosen from the color function defined above
            .attr("d", arc);                                    //this creates the actual SVG path using the associated data (pie) with the arc drawing function

        arcs.append("svg:text")                                     //add a label to each slice
            .attr("transform", function (d) {                    //set the label's origin to the center of the arc
                //we have to make sure to set these before calling arc.centroid
                d.innerRadius = r;
                d.outerRadius = r + 20;
                return "translate(" + arc.centroid(d) + ")";        //this gives us a pair of coordinates like [50, 50]
            })
            .attr("text-anchor", "middle")                          //center the text on it's origin
            .text(function (d, i) {
                return data[i].label;
            });        //get the label from our original data array

        arcs.append("svg:text")                                     //add percentage to each label
            .attr("transform", function (d) {                    //set the label's origin to the center of the arc
                //we have to make sure to set these before calling arc.centroid
                d.innerRadius = r;
                d.outerRadius = r + 20;
                var coords = arc.centroid(d);
                coords[1] = coords[1] + 14;
                return "translate(" + coords + ")";        //this gives us a pair of coordinates like [50, 50]
            })
            .attr("text-anchor", "middle")                          //center the text on it's origin
            .text(function (d, i) {
                return "(" + data[i].value * 100 + "%)";
            });        //get the label from our original data array
    });
}

function buildDotChart() {
    function truncate(str, maxLength, suffix) {
        if (str.length > maxLength) {
            str = str.substring(0, maxLength + 1);
            str = str.substring(0, Math.min(str.length, str.lastIndexOf(" ")));
            str = str + suffix;
        }
        return str;
    }

    $("#DotChart").empty();

    var margin = {top: 20, right: 200, bottom: 0, left: 50},
        width = chartwidth / 2,
        height = 650;

    var x_start = 0,
        x_end = 2;

    var c = LMColor();

    var x = d3.scale.linear()
        .domain([0, 1, 2])
        .range([0, width, width*2]);

    const tickLabels = {
        0: 'On the lease',
        1: 'Off the lease',
        2: 'None'
    };

    var xAxis = d3.svg.axis()
        .scale(x)
        .tickFormat(function(d) {
            return tickLabels[d]
        })
        .orient("top");

    var svg = d3.select("#DotChart").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .style("margin-left", margin.left + "px")
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var demodata = [{
        "intentions": [[0, 10], [1, 6], [2, 4]],
        "total": 20,
        "name": "Agriculture"
    }, {
        "intentions": [[0, 5], [1, 6], [2, 1]],
        "total": 12,
        "name": "Forestry"
    }, {
        "intentions": [[0, 4], [1, 5], [2, 1]],
        "total": 10,
        "name": "Mining"
    }, {
        "intentions": [[0, 4], [1, 8], [2, 3]],
        "total": 15,
        "name": "Tourism"
    }];

    d3.json('', function (data) {
        data = demodata;

        x.domain([x_start, x_end]);
        var xScale = d3.scale.linear()
            .domain([x_start, x_end])
            .range([0, width]);

        svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(-10," + 0 + ")")
            .attr("fill", "#4a4a4a")
            .call(xAxis);

        for (var j = 0; j < data.length; j++) {
            var g = svg.append("g").attr("class", "intention");

            var circles = g.selectAll("circle")
                .data(data[j]['intentions'])
                .enter()
                .append("circle");

            var text = g.selectAll("text")
                .data(data[j]['intentions'])
                .enter()
                .append("text");

            var rScale = d3.scale.linear()
                .domain([0, d3.max(data[j]['intentions'], function (d) {
                    return d[1];
                })])
                .range([2, 9]);

            circles
                .attr("cx", function (d, i) {
                    return xScale(d[0]);
                })
                .attr("cy", j * 20 + 20)
                .attr("r", function (d) {
                    return rScale(d[1]);
                })
                .style("fill", function (d) {
                    return c(j);
                });

            text
                .attr("y", j * 20 + 25)
                .attr("x", function (d, i) {
                    return xScale(d[0]) - 5;
                })
                .attr("class", "value")
                .text(function (d) {
                    return d[1];
                })
                .style("fill", function (d) {
                    return c(j);
                })
                .style("display", "none");

            g.append("text")
                .attr("y", j * 20 + 25)
                .attr("x", width + 20)
                .attr("class", "label")
                .text(truncate(data[j]['name'], 30, "..."))
                .style("fill", function (d) {
                    return c(j);
                })
                .on("mouseover", mouseover)
                .on("mouseout", mouseout);
        }

        function mouseover(p) {
            var g = d3.select(this).node().parentNode;
            d3.select(g).selectAll("circle").style("display", "none");
            d3.select(g).selectAll("text.value").style("display", "block");
        }

        function mouseout(p) {
            var g = d3.select(this).node().parentNode;
            d3.select(g).selectAll("circle").style("display", "block");
            d3.select(g).selectAll("text.value").style("display", "none");
        }
    });
}

function buildAgriculturalPies() {
    RGraph.ObjectRegistry.Clear();
    var query_params = get_query_params(get_base_filter(), get_filter());
    var json_query = "/api/agricultural-produce.json" + query_params;
    jQuery.getJSON(json_query, function (data) {
        // show/hide data availability
        var sum = 0;
        $(data).each(function (i) {
            sum += data[i].available + data[i].not_available;
        });
        sum && $(".data-availability, .data").show() || $(".data-availability, .data").hide();

        var pie_data = [];
        for (var i = 0; i < data.length; i++) {
            pie_data = [];
            $('#pie-' + data[i]["region"]).parent().next().find('.food-crop').text(data[i]["agricultural_produce"]["food_crop"] + "%" + " (" + numberWithCommas(data[i]["hectares"]["food_crop"]) + " ha)");
            $('#pie-' + data[i]["region"]).parent().next().find('.non-food-crop').text(data[i]["agricultural_produce"]["non_food"] + "%" + " (" + numberWithCommas(data[i]["hectares"]["non_food"]) + " ha)");
            $('#pie-' + data[i]["region"]).parent().next().find('.flex-crop').text(data[i]["agricultural_produce"]["flex_crop"] + "%" + " (" + numberWithCommas(data[i]["hectares"]["flex_crop"]) + " ha)");
            $('#pie-' + data[i]["region"]).parent().next().find('.multiple-crop').text(data[i]["agricultural_produce"]["multiple_use"] + "%" + " (" + numberWithCommas(data[i]["hectares"]["multiple_use"]) + " ha)");
            var sum = data[i]["hectares"]["food_crop"] + data[i]["hectares"]["non_food"] + data[i]["hectares"]["flex_crop"] + data[i]["hectares"]["multiple_use"];
            $('#pie-' + data[i]["region"]).closest(".row").prev().find("h2 span").text("(" + numberWithCommas(sum) + " ha)");
            pie_data.push(data[i]["agricultural_produce"]["food_crop"]);
            pie_data.push(data[i]["agricultural_produce"]["non_food"]);
            pie_data.push(data[i]["agricultural_produce"]["flex_crop"]);
            pie_data.push(data[i]["agricultural_produce"]["multiple_use"]);

            var pie = new RGraph.Pie('pie-' + data[i]["region"], pie_data);
            pie.Set('chart.colors', ['#060c0f', '#225559', '#46b2bf', '#acd4dc']);
            pie.Set('chart.strokestyle', '#bbb');
            pie.Set('chart.text.font', 'Open Sans');
            pie.Set('chart.text.size', '9');
            if (data[i]["region"] == "overall") {
                pie.Set('chart.radius', 209);
                pie_data = []
                pie_data.push(data[i]["available"]);
                pie_data.push(data[i]["not_available"]);
                var pie2 = new RGraph.Pie('pie-availability', pie_data);
                pie2.Set('chart.colors', ['#1e1e1e', '#828282;']);
                pie2.Set('chart.radius', 15);
                pie2.Set('chart.strokestyle', '#bbb');
                pie2.Set('chart.text.font', 'Open Sans');
                pie2.Set('chart.text.size', '9');
                RGraph.Effects.Fade.In(pie2, {'duration': 250});
                var sum = data[i]["available"] + data[i]["not_available"],
                    available_per = parseInt(data[i]["available"] / sum * 100, 10),
                    not_available_per = parseInt(data[i]["not_available"] / sum * 100, 10);
                $("ul.legend:first li:first span").text(" (" + numberWithCommas(data[i]["available"]) + " hectares, " + available_per + "%)");
                $("ul.legend:first li:last span").text(" (" + numberWithCommas(data[i]["not_available"]) + " hectares, " + not_available_per + "%)");
            } else {
                pie.Set('chart.radius', 45);
            }
            RGraph.Effects.Fade.In(pie, {'duration': 250});
        }
    });
}

$(document).ready(function() {
    chartwidth = $('#chartarea').width();
});