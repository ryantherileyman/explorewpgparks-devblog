+++
date = "2025-11-30T09:36:00-05:00"
draft = false
title = "Creating Map Animations with LeafletJS"
show_description = false
description = "Creating video clips of animated maps using a web browser and OBS."
images = [ "leaflet-map-animations-post-og-image.jpg",]
tags = [ "animation", "web-development",]
hashnode-cover-image = "leaflet-map-animations-post-cover-image.jpg"
github-status = "published"
hashnode-status = "published"
hashnode-slug = "creating-map-animations-with-leafletjs"
+++
Welcome!

Over the past few months, I've built myself a neat little prototype that lets me create video clips of map animations using [LeafletJS](https://leafletjs.com/).  I've used this to create several Youtube videos over on my [Exploring Winnipeg Parks Youtube Channel](https://www.youtube.com/@ExploringWinnipegParks), when I'm explaining details about the location of parks or neighbourhoods.

![Screenshot from a Sample Map Animation](map-animation-screenshot-01.jpg)

The entire process uses several technologies:
1. Python scripts using the [Overpass API](https://overpass-api.de/) and [OpenRouteService](https://openrouteservice.org/) API to fetch geometries that I want to draw on the map.  Both of these API's make use of [OpenStreetMap](https://www.openstreetmap.org/), the map database maintained by a global community of volunteers.
2. The [Shapely](https://pypi.org/project/shapely/) Python library to manipulate geometric shapes, and the [PyProj](https://proj.org/en/stable/) Python library to handle geospatial co-ordinates.
3. The [LeafletJS](https://leafletjs.com/) JavaScript library to display interactive maps in a web browser window.
4. A custom JavaScript prototype driven by a [requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame) loop, and a custom JSON file that describes the map animation steps to perform.
5. [OBS Studio](https://obsproject.com/) to record the browser window into a video file.
6. Any video editing software of your choice.  I use an old version of Corel VideoStudio, but if you're looking for a free open-source video editor, you can try out [Kdenlive](https://kdenlive.org/).

## LeafletJS and the Web Browser

[LeafletJS](https://leafletjs.com/) is typically used by websites that want to embed a map, displaying the location of their business or other points of interest.  I used it extensively on the [Exploring Winnipeg Parks](https://www.exploringwinnipegparks.ca/) website to display the location of parks, with map markers for points of interest and nearby bus stops.

LeafletJS provides a full-featured API for performing pan and zoom animations, displaying markers, and drawing paths or polygons over top of the map.

Modern web browsers provide plenty of native technologies that can be used to perform animations:
1. The CSS [animation](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/animation) property and [@keyframes](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@keyframes) rule can provide precise control over animation sequences and transitions.
2. [SVG](https://developer.mozilla.org/en-US/docs/Web/API/SVGElement) elements can be used to draw complex shapes, and CSS applies to them like any other HTML element.
3. The [Canvas API](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API) allows for more complex 2D graphics.
4. The [Web Animations API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API) is something I was unaware of, right up until I was researching how others might be using web browsers to create video content.  It apparently gained widespread browser support by about 2020, and is something I'll have to look into!

## Using the OpenRouteService API

[OpenRouteService Maps](https://maps.openrouteservice.org/) is a fantastic online tool for visually generating routes on a map.  It leverages all of the map data from [OpenStreetMap](https://www.openstreetmap.org/), meaning it knows all about roadways, walking paths, and rivers.  You can right-click on the map to declare each of your waypoints, and it calculates a route based on whether you want directions for walking, cycling, driving, or even wheelchair access.  You can then download the file in one of several standardized formats, such as JSON.

To access the OpenRouteService API, you'll need to set up an account and request an API key.  For casual use, currently up to 7000 requests per day as of this writing, this is a free service.

The API can be accessed using an HTTP client.  Here's a short example in Python, where `profile` identifies whether you want instructions for driving (`driving-car`), walking (`foot-walking`), cycling (`cycling-regular`), etc.  The `waypoints` is expected to be an array of `[lon, lat]` pairs.  The `ORS_API_KEY` is expected to be defined elsewhere, and should be retrieved from a secure place.

```
import httpx
from shapely.geometry import LineString

def get_ors_route(profile, waypoints):
    url = f"https://api.openrouteservice.org/v2/directions/{profile}/geojson"
    headers = { "Authorization": ORS_API_KEY }
    body = { "coordinates": waypoints }
    with httpx.Client() as client:
        response = client.post(url, headers=headers, json=body)
        response.raise_for_status()
        response_data = response.json()
    output_coords = response_data["features"][0]["geometry"]["coordinates"]
    return LineString(output_coords)
```

The JSON response provides plenty of other information besides just the coordinates of the line segment, such as distance, approximate duration, and human-readable instructions.  The above example is only extracting the line segment that you would display on a map.  The OpenRouteService website provides an API Playground, where you can try out the API with full documentation.

## JavaScript Animation Engine

My JavaScript animation engine makes use of the native [requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame) method.  This is commonly used by web-based games to control their game loop.  For my map animation engine, the basic pattern was as follows:

```
class LeafletAnimationManager {
    #leafletMap;
    constructor(containerElement) {
        this.#leafletMap = // initialize LeafletJS
    }
    runAnimation() {
        // Set start time with a 3-second buffer
        let startTime = performance.now() + 3000;
        requestAnimationFrame(this.#frameTick.bind(this));
    }
    #frameTick(now) {
        const elapsedTime = now - this.#startTime;
        const currFrame = Math.floor(elapsedTime / (1000 / 30)); // 30 FPS

        // Display a "countdown" for the first 3 seconds
        if ( currFrame < 0 ) {
            // Set textContent of a countdown <div> to currFrame
        } else {
            // Hide the countdown <div>
        }

        // Inspect map animation instructions, and trigger map animations as needed

        requestAnimationFrame(this.#frameTick.bind(this));
    }
}
```

I organized the map animation instructions into a simple array of custom objects.  Each object tells the engine what animation action to perform, when to trigger it, and any additional information specific to the action.  Thus far, I have a very small subset of actions that I support:
1. `fly-to` will call LeafletJS `flyTo()` with a given latitude, longitude, zoom, and animation duration.
2. `toggle-marker` will either show or hide a map marker, by adding or removing a CSS class name.  It will also call `bindPopup()` / `openPopup()`, or `closePopup()`, if popup text was provided.
3. `toggle-path` will either show or hide a polygon or polyline, also by adding or removing a CSS class name.
4. `animate-path` extends `toggle-path` by also animating a polyline.  It recalculates the polyline's vertex list each frame using a standard technique called polyline interpolation (also known in GIS as linear referencing).

Once I've formalized my implementation, and added support for more features, I plan to build a web-based animation editor that can be run via a local web server.

## Conclusion

I'm quite pleased with the results so far, and plan to continue to build on what I've done over this upcoming winter.  I'm looking to expand the idea by going beyond just map-related animations, leveraging the web browser's flexbox and CSS capabilities.

My "2025 Year in Review" video showcases the `fly-to` and `toggle-marker` animations:
[![Exploring Winnipeg Parks - 2025 Year in Review](https://img.youtube.com/vi/m_fKvOsdG1M/maxresdefault.jpg)](https://www.youtube.com/watch?v=m_fKvOsdG1M)

My "Oaks Forest Walkthrough" video showcases the `toggle-path` and `animate-path` animations:
[![Exploring Winnipeg Parks - Oaks Forest Walkthrough](https://img.youtube.com/vi/pyf7OcE4QXg/maxresdefault.jpg)](https://www.youtube.com/watch?v=pyf7OcE4QXg)

While researching what others might be doing as it relates to creating map animation content, I found a rather intriquing [academic article](https://arxiv.org/html/2505.21966v1) about an LLM-based tool called MapStory.  You can find its home page on the University of Colorado Boulder's ATLAS Institute at [MapStory](https://www.colorado.edu/atlas/mapstory).  I'll be curious to see how this project progresses!
