
      function initMap() {
        var markers = {{ markers|tojson }};

        var firstMarker = markers[0];
        var map = new google.maps.Map(document.getElementById('map'), {
          zoom: 8,
          center: firstMarker
        });

        // Add a marker to the map for each food post location
        {% for marker in markers %}
        new google.maps.Marker({
          position: {{ marker|tojson|safe }},
          map: map
        });
        {% endfor %}
      }
