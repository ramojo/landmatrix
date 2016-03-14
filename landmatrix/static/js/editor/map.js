var geocoders = new Array();
var maps = {};
var views = {};
var markers = new Array();
var autocompletes = new Array();
var latChanged = new Array();
var lonChanged = new Array();
var lock = true;;

$(document).ready(function () {
    $(".maptemplate").each(function (index) {
        $(this).attr('id', 'map' + (index + 1)).removeClass("maptemplate").addClass("map");
        initializeMap(index + 1);
    });

    $('#accordion').on("shown.bs.collapse", function(things) {
        var mapId = String(things.target.id).split("_")[1];
        //console.log("collapsehandler: ", mapId, maps);
        var map = maps[mapId];
        if (typeof map !== 'undefined') {
            map.updateSize();
        }
    });
});

function unlockMaps() {
    lock = false;
}

function getLocationFields(mapId) {
    const target = "map" + mapId;

    var result = {
        lat: $(".point_lat input"),
        lon: $(".point_lon input")
    };

    return result;
}

function updateMapLocation(mapId) {
    if (lock == false) {

        var fields = getLocationFields(mapId);

        var lat = 0.0;
        lat =  parseFloat(fields.lat.val());

        var lon = 0.0;
        lon = parseFloat(fields.lon.val());

        if (isNaN(lat) || isNaN(lon)) {
            lon = lat = 0;
        }

        var center = ol.proj.fromLonLat([lon, lat]);
        markers[mapId].setCoordinates(center);
        views[mapId].setCenter(center);
        updateGeocoding(mapId);
    }
}

function updateLocationFields(mapId, coords) {
    if (lock == false) {
        // Adjust marker
        markers[mapId].setCoordinates(coords);

        // Set center of mapview
        var view = views[mapId];
        view.setCenter(coords);

        // Update form fields with converted coords
        var formCoords = ol.proj.toLonLat(coords);

        var fields = getLocationFields(mapId);

        fields.lat.val(formCoords[1]);
        fields.lon.val(formCoords[0]);
        updateGeocoding(mapId);
    }
}

function updateGeocoding(mapId) {
    var fields = getLocationFields(mapId);
    var latLng = new google.maps.LatLng(fields.lat, fields.lon);

    var map = maps[mapId];

    // changed lan or lon value, request target Country

    console.log("Hello, i'm updating")

    var accuracy = $(map).parents("div.panel-body").find(".level_of_accuracy select :selected").first().val();
    console.log(accuracy)
    if (accuracy == "40" && fields.lat != null && fields.lat != "" && fields.lon != null && fields.lon != "") {

        geocoders[index].geocode({"latLng" : latLng, "language": "en"}, function(results, status) {
            for(var i = 0; i < results[0].address_components.length; i++) {
                if (results[0].address_components[i].types.indexOf("country") != -1) {
                    country = results[0].address_components[i].short_name;
                    $(this).parents("div").find(".target_country option[title='" + country + "']").attr('selected', 'selected');
                    $(this).parents("div").find(".target_country option:not([title='" + country + "'])").removeAttr("selected");
                }
            }
        });
    } else {
        console.log("NOT updating anything")
    }

    //switched level of accuracy fire event on lan and lon input fields
    $(map).parents("div").find(".level_of_accuracy select").change(function() {
        if ($(map).find(":selected").val() == "40") {
            $(map).parents("div").find(".point_lat input, .point_lon input").change();
        }
    });

}

var markerStyle = new ol.style.Style({
    text: new ol.style.Text({
        text: '\uf041',
        font: 'normal 36px FontAwesome',
        textBaseline: 'Bottom',
        fill: new ol.style.Fill({
          color: '#4bbb87'
        })
     })
});


function initializeMap (mapId) {
    const target = "map" + mapId;

    var fields = getLocationFields(mapId);

    var lat = 0.0;
    lat =  parseFloat(fields.lat.val());

    var lon = 0.0;
    lon = parseFloat(fields.lon.val());

    if (isNaN(lat) || isNaN(lon)) {
        lon = lat = 0;
    }

    var center = ol.proj.fromLonLat([lon, lat]);

    var view = new ol.View({
        center: center,
        zoom: 5,
        minZoom: 2,
        maxZoom: 17
    });

    var marker = new ol.geom.Point(center);

    var feature = new ol.Feature({
        geometry: marker
    });

    feature.setStyle(markerStyle);

    var source = new ol.source.Vector({
        features: [feature]
    });

    var vectorLayer = new ol.layer.Vector({
        source: source
    });

    var map = new ol.Map({
       target: target,
       layers: [
            new ol.layer.Tile({
                title: 'OpenStreetMap',
                type: 'base',
                visible: true,
                source: new ol.source.OSM()
            }),
            vectorLayer
        ],
        view: view
    });


    maps[mapId] = map;
    views[mapId] = view;
    markers[mapId] = marker;
    geocoders[mapId] = new google.maps.Geocoder();

    map.on('singleclick', function(evt) {
        updateLocationFields(mapId, evt.coordinate);
    });


    fields.lon.change(function() {
        updateMapLocation(mapId);
    });

    fields.lat.change(function() {
        updateMapLocation(mapId);
    });

}


function legacyInitializeMap(el, index) {
  //MAP
  var latlng = new google.maps.LatLng(41.659,-4.714);
  var options = {
    zoom: 16,
    center: latlng,
    mapTypeId: google.maps.MapTypeId.SATELLITE
  };
  maps[index] = new google.maps.Map(el, options);
  //GEOCODER
  geocoders[index] = new google.maps.Geocoder();

  markers[index] = new google.maps.Marker({
    map: maps[index],
    draggable: true
  });
  var lat = $(el).parents("ul").find(".point_lat input").val();
  var lon = $(el).parents("ul").find(".point_lon input").val();
  var latLng = new google.maps.LatLng(lat, lon);
  maps[index].setCenter(latLng);
  markers[index].setPosition(latLng);
  latChanged[index] = lat;
  lonChanged[index] = lon;
  if(lat.length == 0) {
    maps[index].setZoom(2);
  } else {
    maps[index].setZoom(5);
  }
  // changed lan or lon value, center map and request target Country
  $(el).parents("ul").find(".point_lat input, .point_lon input").change(function() {
    var accuracy = $(this).parents("ul").find(".level_of_accuracy select :selected").first().val();
    var value = $(this).val();
    if ($(this).parents("li").hasClass("point_lat")) {
      latChanged[index] = value;
    } else {
      lonChanged[index] = value;
    }
    if (accuracy == "40" && latChanged[index] != null && latChanged[index] != "" && lonChanged[index] != null && lonChanged[index] != "") {
      var latLng = new google.maps.LatLng(latChanged[index], lonChanged[index]);
      maps[index].setCenter(latLng);
      maps[index].setZoom(8);
      markers[index].setPosition(latLng);
      geocoders[index].geocode({"latLng" : latLng, "language": "en"}, function(results, status) {
        for(var i = 0; i < results[0].address_components.length; i++) {
            if (results[0].address_components[i].types.indexOf("country") != -1) {
              country = results[0].address_components[i].short_name;
              $(el).parents("ul").find(".target_country option[title='" + country + "']").attr('selected', 'selected');
              $(el).parents("ul").find(".target_country option:not([title='" + country + "'])").removeAttr("selected");
            }
          };
      });
    }
  });
  //switched level of accuracy fire event on lan and lon input fields
  $(el).parents("ul").find(".level_of_accuracy select").change(function() {
    if ($(this).find(":selected").val() == "40") {
      $(this).parents("ul").find(".point_lat input, .point_lon input").change();
    }
  });
  google.maps.event.addListener(markers[index], 'drag', function() {
  geocoders[index].geocode({'latLng': markers[index].getPosition(), "language": "en"}, function(results, status) {
    if (status == google.maps.GeocoderStatus.OK) {
      if (results[0]) {
        $(el).parents("ul").find(".point_lat input").val(markers[index].getPosition().lat());
        $(el).parents("ul").find(".point_lon input").val(markers[index].getPosition().lng());
      }
    }
  });
});
}


function init_google_maps(el, index) {
  el.autocomplete({
        //This bit uses the geocoder to fetch address values
        source: function(request, response) {
          var accuracy = el.parents("ul").find(".level_of_accuracy select :selected").first().val();
          // only lookup name when level of accuracy is not exact coordinates
          if (accuracy != "40") {
            geocoders[index].geocode( {'address': request.term, "language": "en" }, function(results, status) {
              response($.map(results, function(item) {
                country = "";
                for(var i = 0; i < item.address_components.length; i++) {
                  if (item.address_components[i].types.indexOf("country") != -1) {
                    country = item.address_components[i].short_name;
                  }
                };
                return {
                  label:  item.formatted_address,
                  value: item.formatted_address,
                  latitude: item.geometry.location.lat(),
                  longitude: item.geometry.location.lng(),
                  country: country
                }
              }));
            })
          }
        },
        //This bit is executed upon selection of an address
        select: function(event, ui) {
          el.parents("ul").find(".point_lat input").val(ui.item.latitude).change();
          el.parents("ul").find(".point_lon input").val(ui.item.longitude).change();
          //$("#id_spatial_data-target_country option:selected").removeAttr("selected"); - doesn't work in FF 14
          el.parents("ul").find(".target_country option[title='" + ui.item.country + "']").attr('selected', 'selected');
          el.parents("ul").find(".target_country option:not([title='" + ui.item.country + "'])").removeAttr("selected");
          var location = new google.maps.LatLng(ui.item.latitude, ui.item.longitude);
          markers[index].setPosition(location);
          maps[index].setCenter(location);
        }
      });
};
