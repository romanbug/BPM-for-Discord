#!/usr/bin/python
# -*- coding: utf8 -*-
################################################################################
##
## Copyright (C) 2012 Typhos
##
## This Source Code Form is subject to the terms of the Mozilla Public
## License, v. 2.0. If a copy of the MPL was not distributed with this
## file, You can obtain one at http://mozilla.org/MPL/2.0/.
##
################################################################################

import argparse
import functools
import json
import os
import os.path
import random
import string
import StringIO
import urllib

import flask
from flask import request
import yaml

import bplib
import bplib.objects
import bpgen

all_tags = []   # sorted set
css_cache = {}  # source_name -> str

def info_for(emote):
    if hasattr(emote, "image_url"):
        return (emote.image_url, emote.offset[1], emote.offset[0], emote.size[0], emote.size[1])
    else:
        return (-1, -1, -1, -1)

def make_tag_list():
    global all_tags
    tmp = set()
    for source in data_manager.sources.values():
        for emote in source.emotes.values():
            tmp |= emote.tags
    all_tags = sorted(tmp)

data_manager = bplib.objects.DataManager()
data_manager.load_all_sources()
make_tag_list()

def sync_tags(source):
    path = "tags/%s.yaml" % (source.name.split("/")[-1])
    file = open(path, "w")
    yaml.dump(source.dump_tag_data(data_manager), file)

def get_css(source_name):
    if source_name not in css_cache:
        css_rules = bpgen.build_css(data_manager.sources[source_name].emotes.values())
        stream = StringIO.StringIO()
        bpgen.dump_css(stream, css_rules)
        css_cache[source_name] = stream.getvalue()
    return css_cache[source_name]

def url_quote(s):
    return urllib.quote(s, "")

app = flask.Flask(__name__, static_folder="tagapp-static", static_url_path="/static")
app.jinja_env.globals["sorted"] = sorted
app.jinja_env.globals["urlquote"] = url_quote

secret_key = "".join(random.choice(string.letters) for _ in range(32))
print("SECRET KEY: %s" % (secret_key))

def check_auth(username, password):
    return str(username) == "admin" and str(password) == secret_key

def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return flask.Response("Access denied", 401, {"WWW-Authenticate": "Basic realm=\"Login Required\""})
        return f(*args, **kwargs)
    return decorated

@app.route("/")
def index():
    return flask.render_template("index.html", sources=sorted(data_manager.sources), all_tags=all_tags)

@app.route("/source/<source_name>")
def tag(source_name):
    source_name = urllib.unquote(str(source_name))
    source = data_manager.sources[source_name]
    emotes = list(source.unignored_emotes(data_manager))
    given_emotes = {}
    for emote in emotes:
        info = info_for(emote)
        given_emotes.setdefault(info, []).append(emote)
    for info in given_emotes:
        given_emotes[info].sort()
    tags = {emote.name: sorted(emote.tags) for emote in emotes}
    return flask.render_template("tag.html", source=source, given_emotes=sorted(given_emotes.items()), tags=tags)

@app.route("/source/<source_name>/write", methods=["POST"])
def write(source_name):
    source_name = urllib.unquote(str(source_name))
    data = json.loads(request.form["tags"])
    source = data_manager.sources[source_name]
    for (name, tags) in data.items():
        assert isinstance(name, unicode)
        assert isinstance(tags, list) and all([isinstance(r, unicode) for r in tags])
        source.emotes[str(name)].tags = set(map(str, tags))
    sync_tags(source)
    make_tag_list()
    return flask.redirect(flask.url_for("index"))

@app.route("/source/<source_name>/css")
def css(source_name):
    source_name = urllib.unquote(str(source_name))
    return flask.Response(get_css(source_name), mimetype="text/css")

@app.route("/tag/<tag>")
def taginfo(tag):
    tag = str(tag)
    data = {}
    for source in data_manager.sources.values():
        data[source] = []
        for emote in source.unignored_emotes(data_manager):
            if tag in emote.tags:
                data[source].append(emote)
        data[source].sort(key=lambda e: e.name)
        if not data[source]:
            del data[source]
    data = sorted(data.items(), key=lambda i: i[0].name)
    return flask.render_template("taginfo.html", tag=tag, data=data)

@app.route("/tag/<tag>/rename", methods=["POST"])
@requires_auth
def rename_tag(tag):
    tag = str(tag)
    to = str(request.form["to"])
    if not to.startswith("+"):
        to = "+" + to
    for (source_name, source) in data_manager.sources.items():
        dirty = False
        for (name, emote) in source.emotes.items():
            if tag in emote.tags:
                emote.tags.remove(tag)
                emote.tags.add(to)
                dirty = True
        if dirty:
            sync_tags(source)
    all_tags.remove(tag)
    if to not in all_tags:
        all_tags.append(to)
        all_tags.sort()
    return flask.redirect(flask.url_for("taginfo", tag=to))

@app.route("/tag/<tag>/delete", methods=["POST"])
@requires_auth
def delete_tag(tag):
    tag = str(tag)
    if not tag.startswith("+"):
        tag = "+" + tag
    for (source_name, source) in data_manager.source.items():
        dirty = False
        for (name, emote) in source.emotes.items():
            if tag in emote.tags:
                emote.tags.remove(tag)
                dirty = True
        if dirty:
            sync_tags(source)
    all_tags.remove(tag)
    return flask.redirect(flask.url_for("index"))

def main():
    parser = argparse.ArgumentParser(description="Emote tagger webapp")
    parser.add_argument("-d", "--debug", help="Enable debug mode", default=False, action="store_true")
    args = parser.parse_args()

    app.debug = args.debug

    app.run()

if __name__ == "__main__":
    main()
