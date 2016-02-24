//Coordinates : need to CONVERT the projections from ... to ... :
//EPSG:4326: is the WGS84 projection, commun use for the World (ex: GPS)
//EPSG:3857:Spherical Web Mercator projection used by Google and OpenStreetMap

// Globale Variablen 
var map;

var markerSource = new ol.source.Vector();

var clusterSource = new ol.source.Cluster({
    distance: 50,
    source: markerSource
});

var layers = [];

var intentions = [
    'Agriculture',
    'Forestry',
    'Conservation',
    'Industry',
    'Renewable Energy',
    'Tourism',
    'Other',
    'Mining',
];


var intentionColors = {
    'Agriculture': '#1D6914',
    'Forestry': '#2A4BD7',
    'Conservation': '#575757',
    'Industry': '#AD2323',
    'Renewable Energy': '#81C57A',
    'Tourism': '#9DAFFF',
    'Other': '#8126C0',
    'Mining': '#814A19',
    'Undefined': '#FF0000'
};


//Map, Layers and Map Controls
$(document).ready(function () {

    // Set up popup

    /**
     * Elements that make up the popup.
     */
    var container = document.getElementById('popup');
    var content = document.getElementById('popup-content');
    var closer = document.getElementById('popup-closer');

    /**
     * Create an overlay to anchor the popup to the map.
     */
    var PopupOverlay = new ol.Overlay(/** @type {olx.OverlayOptions} */ ({
        element: container,
        autoPan: true,
        autoPanAnimation: {
            duration: 250
        }
    }));

    var closePopup = function () {
        PopupOverlay.setPosition(undefined);
        closer.blur();
        return false;
    };

    /**
     * Add a click handler to hide the popup.
     * @return {boolean} Don't follow the href.
     */
    closer.onclick = closePopup;


    /**
     * GeoJSON features
     *
     */

    var image = new ol.style.Circle({
        radius: 5,
        fill: null,
        stroke: new ol.style.Stroke({color: 'red', width: 1})
    });

    var styles = {
        'Point': [new ol.style.Style({
            image: image
        })],
        'LineString': [new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: 'green',
                width: 1
            })
        })],
        'MultiLineString': [new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: 'green',
                width: 1
            })
        })],
        'MultiPoint': [new ol.style.Style({
            image: image
        })],
        'MultiPolygon': [new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: 'yellow',
                width: 1
            }),
            fill: new ol.style.Fill({
                color: 'rgba(255, 255, 0, 0.1)'
            })
        })],
        'Polygon': [new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: 'blue',
                lineDash: [4],
                width: 3
            }),
            fill: new ol.style.Fill({
                color: 'rgba(0, 0, 255, 0.1)'
            })
        })],
        'GeometryCollection': [new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: 'magenta',
                width: 2
            }),
            fill: new ol.style.Fill({
                color: 'magenta'
            }),
            image: new ol.style.Circle({
                radius: 10,
                fill: null,
                stroke: new ol.style.Stroke({
                    color: 'magenta'
                })
            })
        })],
        'Circle': [new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: 'red',
                width: 2
            }),
            fill: new ol.style.Fill({
                color: 'rgba(255,0,0,0.2)'
            })
        })]
    };

    var styleFunction = function (feature, resolution) {
        return styles[feature.getGeometry().getType()];
    };

    /*
     var geojsonObject = {
     'type': 'FeatureCollection',
     'crs': {
     'type': 'name',
     'properties': {
     'name': 'EPSG:3857'
     }
     },
     'features': [{
     'type': 'Feature',
     'geometry': {
     'type': 'Point',
     'coordinates': [0, 0]
     }
     }, {
     'type': 'Feature',
     'geometry': {
     'type': 'LineString',
     'coordinates': [[4e6, -2e6], [8e6, 2e6]]
     }
     }, {
     'type': 'Feature',
     'geometry': {
     'type': 'LineString',
     'coordinates': [[4e6, 2e6], [8e6, -2e6]]
     }
     }, {
     'type': 'Feature',
     'geometry': {
     'type': 'Polygon',
     'coordinates': [[[-5e6, -1e6], [-4e6, 1e6], [-3e6, -1e6]]]
     }
     }, {
     'type': 'Feature',
     'geometry': {
     'type': 'MultiLineString',
     'coordinates': [
     [[-1e6, -7.5e5], [-1e6, 7.5e5]],
     [[1e6, -7.5e5], [1e6, 7.5e5]],
     [[-7.5e5, -1e6], [7.5e5, -1e6]],
     [[-7.5e5, 1e6], [7.5e5, 1e6]]
     ]
     }
     }, {
     'type': 'Feature',
     'geometry': {
     'type': 'MultiPolygon',
     'coordinates': [
     [[[-5e6, 6e6], [-5e6, 8e6], [-3e6, 8e6], [-3e6, 6e6]]],
     [[[-2e6, 6e6], [-2e6, 8e6], [0, 8e6], [0, 6e6]]],
     [[[1e6, 6e6], [1e6, 8e6], [3e6, 8e6], [3e6, 6e6]]]
     ]
     }
     }, {
     'type': 'Feature',
     'geometry': {
     'type': 'GeometryCollection',
     'geometries': [{
     'type': 'LineString',
     'coordinates': [[-5e6, -5e6], [0, -5e6]]
     }, {
     'type': 'Point',
     'coordinates': [4e6, -5e6]
     }, {
     'type': 'Polygon',
     'coordinates': [[[1e6, -6e6], [2e6, -4e6], [3e6, -6e6]]]
     }]
     }
     }]
     };
     */

    var geojsonObject = {
        'type': 'FeatureCollection',
        'crs': {
            'type': 'name',
            'properties': {
                'name': 'EPSG:3857'
            }
        },
        'features': []/*{
         'type': 'Feature',
         'geometry': {
         'type': 'Polygon',
         'coordinates': [[[-5e6, -1e6], [-4e6, 1e6], [-3e6, -1e6]]]
         }
         }]*/
    };

    var vectorSource = new ol.source.Vector({
        features: (new ol.format.GeoJSON()).readFeatures(geojsonObject)
    });

    var vectorLayer = new ol.layer.Vector({
        title: 'GeoJSON',
        visible: true,
        source: vectorSource,
        style: styleFunction
    });


    map = new ol.Map({
        target: 'map',
        // Base Maps Layers. To change the default Layer : "visible: true or false".
        // ol.layer.Group defines the LayerSwitcher organisation
        layers: [
            new ol.layer.Group({
                'title': 'Base Maps',
                layers: [
                    vectorLayer,
                    new ol.layer.Tile({
                        title: 'OpenStreetMap',
                        type: 'base',
                        visible: true,
                        source: new ol.source.OSM()
                    }),
                    new ol.layer.Tile({
                        title: 'Satellite',
                        type: 'base',
                        visible: false,
                        source: new ol.source.MapQuest({layer: 'sat'})
                    }),
                    new ol.layer.Tile({
                        title: 'Toner',
                        type: 'base',
                        visible: false,
                        source: new ol.source.Stamen({layer: 'toner'})
                    })
                ]
            }),
            // Context Layers from the Landobservatory Geoserver.
            new ol.layer.Group({
                title: 'Context Layers',
                layers: contextLayers
            })
        ],
        controls: [
            new ol.control.FullScreen(),
            new ol.control.Zoom(),
            new ol.control.ScaleLine(),
            new ol.control.MousePosition({
                projection: 'EPSG:4326',
                coordinateFormat: function (coordinate) {
                    return ol.coordinate.format(coordinate, '{y}, {x}', 4);
                }
            }),
            new ol.control.FullScreen(),
            new ol.control.Attribution
            // new ol.control.ZoomToExtent({
            // 				extent:undefined
            // }),
        ],
        interactions: [
            new ol.interaction.Select(),
            new ol.interaction.MouseWheelZoom(),
            new ol.interaction.PinchZoom(),
            new ol.interaction.DragZoom(),
            new ol.interaction.DoubleClickZoom(),
            new ol.interaction.DragPan()
        ],
        overlays: [PopupOverlay],
        // Set the map view : here it's set to see the all world.
        view: new ol.View({
            center: [0, 0],
            zoom: 2
        })
    });

    //var styleCache = {};

    var cluster = new ol.layer.Vector({
        source: clusterSource,
        style: function (feature, resolution) {
            var size = feature.get('features').length;
            //Give a color to each Intention of Investment, only for single points
            // PROBLEM : how to clustered the points by color?

            var color = "";
            var legend_image = {};
            var legend_text = {};
            var style = {};

            if (size > 1) {
                color = '#4C76AB';

                var radius = size + 10;

                if (radius > 30) {
                    radius = 30;
                }
                else if (radius < 10) {
                    radius = 10;
                }

                legend_image = new ol.style.Circle({
                    radius: radius,
                    stroke: new ol.style.Stroke({
                        color: '#fff'
                    }),
                    fill: new ol.style.Fill({
                        color: color
                    })
                });

                legend_text = new ol.style.Text({
                    text: size.toString(),
                    fill: new ol.style.Fill({
                        color: '#fff'
                    })
                });

                style = [new ol.style.Style({
                    image: legend_image,
                    text: legend_text
                })];

            } else {
                feature = feature.get('features')[0];
                var intention = feature.attributes.intention;

                if (intention in intentionColors) {
                    color = intentionColors[intention];
                } else {
                    color = '#000';
                }

                legend_text = new ol.style.Text({
                    text: '\uf041',
                    font: 'normal 36px FontAwesome',
                    textBaseline: 'Bottom',
                    fill: new ol.style.Fill({
                        color: color
                    })
                });

                style = [new ol.style.Style({
                    text: legend_text
                })];

            }

            return style;
        }
    });

    map.addLayer(cluster);
    map.addLayer(vectorLayer);

    // LayerSwitcher Control by https://github.com/walkermatt/ol3-layerswitcher
    var layerSwitcher = new ol.control.LayerSwitcher({
        tipLabel: 'Legende'
    });
    map.addControl(layerSwitcher);
    layerSwitcher.showPanel();

    // Set up intention legend
    var legend = document.getElementById('legend');
    var intentionLegend = document.createElement('ul');

    var legendHeader = document.createElement("label");

    legendHeader.innerHTML = "<strong>Deal Intentions</strong>";
    intentionLegend.appendChild(legendHeader);

    for (intention in intentions) {
        var intentionItem = document.createElement('li');
        var intentionName = intentions[intention];
        var col = intentionColors[intentionName];

        var innerHTML = '<div><span class="legend-symbol" style="color: ' + col + '; background-color: ' + col + ';">.</span>';
        innerHTML = innerHTML + intentionName + "</div>";
        intentionItem.innerHTML = innerHTML;

        intentionLegend.appendChild(intentionItem);
    }

    legend.appendChild(intentionLegend);

    map.on('click', function (evt) {
        var handleFeatureClick = function (feature, layer) {

            var features = feature.getProperties().features;

            if (features.length > 1) {
                content.innerHTML = '<p>Cluster of investments:</p><code>' + features.length + '</code>';

                var deals = {};

                for (feat in features) {
                    var intention = features[feat].attributes.intention;

                    if (intention in deals) {
                        deals[intention]++;
                    } else {
                        deals[intention] = 1;
                    }
                }

                for (dealtype in deals) {
                    content.innerHTML = content.innerHTML + "<br><p>" + dealtype + deals[dealtype] + "</p>";
                }
            } else {
                var feat = features[0];

                // TODO: Here, some javascript should be called to get the deal details from the API
                // and render it inside the actual content popup
                content.innerHTML = '<p>Deal #' + '<p>Coordinates:</p><code>' + feat.attributes.lat.toFixed(4) + ' ' + feat.attributes.lon.toFixed(4) + '</code>' + '<p>Intention of investment:</p><code>' + feat.attributes.intention + '</code>';
            }

            PopupOverlay.setPosition(evt.coordinate);
            return features;
        };

        var PopupFeature = map.forEachFeatureAtPixel(evt.pixel, handleFeatureClick);

        if (PopupFeature) {
        } else {
            closePopup();
        }
    });

    // change Mouse Cursor when over Marker
    var target = map.getTarget();
    var jTarget = typeof target === "string" ? $("#" + target) : $(target);

    $(map.getViewport()).on('mousemove', function (e) {
        var pixel = map.getEventPixel(e.originalEvent);
        var hit = map.forEachFeatureAtPixel(pixel, function (feature, layer) {
            return true;
        });

        if (hit) {
            jTarget.css("cursor", "pointer");
        } else {
            jTarget.css("cursor", "");
        }
    });

    var addData = function (data) {
        console.log('MAP DATA: ', data);
        if (data.length < 1) {
            $('#alert_placeholder').html('<div class="alert alert-warning alert-dismissible" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button><span>There are no deals in the currently displayed region.</span></div>')
        } else {
            for (var i = 0; i < data.length; i++) {
                var marker = data[i];
                addClusteredMarker(parseFloat(marker.point_lon), parseFloat(marker.point_lat), marker.intention);
            }
            console.log('Added deals: ', i);
        }
    };

    $.get(
        "/en/api/deals.json?limit=300", //&investor_country=<country id>&investor_region=<region id>&target_country=<country id>&target_region=<region id>&window=<lat_min,lat_max,lon_min,lon_max>
        addData
    );
});

// MARKERS in clusters. ONE MARKER = ONE DEAL
//longitude, latitude, intention im Index.html definiert
function addClusteredMarker(longitude, latitude, intention) {
    intention = intention || 'Undefined';

    if ((typeof latitude == 'number') && (typeof longitude == 'number')) {
        var feature = new ol.Feature({
            geometry: new ol.geom.Point(ol.proj.transform([longitude, latitude], 'EPSG:4326', 'EPSG:3857'))
        });

        if (intention.indexOf(',') > -1) {
            intention = intention.split(',', 1)[0];
        }

        feature.attributes = {
            intention: intention,
            lat: latitude,
            lon: longitude
        };

        markerSource.addFeature(feature);
    } else {
        console.log("Faulty object: ", longitude, latitude, intention);
    }
}

