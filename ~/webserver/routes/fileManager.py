import os
import flask
from werkzeug.utils import secure_filename

baseD = os.path.abspath(os.path.join(os.path.dirname(__file__), "../shared/"))

def fileManager(subpath=""):
    if flask.session.get('authenticated') != True:
        return flask.redirect('/login')
    
    safe_subpath = os.path.normpath(subpath)

    
    if safe_subpath.startswith("..") or os.path.isabs(safe_subpath):
        flask.flash("Invalid path")
        return flask.redirect(flask.request.referrer or flask.url_for('fileManager_root'))

    curDir = os.path.join(baseD, safe_subpath)
    real_curDir = os.path.realpath(curDir)
    real_baseD = os.path.realpath(baseD)

    
    if not os.path.commonpath([real_baseD, real_curDir]) == real_baseD:
        flask.flash("Invalid path")
        return flask.redirect(flask.request.referrer or flask.url_for('fileManager_root'))

    if not os.path.exists(real_curDir):
        flask.flash("Directory not found")
        return flask.redirect(flask.request.referrer or flask.url_for('fileManager_root'))

    if os.path.isfile(real_curDir):
        rel_dir = os.path.dirname(safe_subpath)
        filename = os.path.basename(safe_subpath)
        return flask.send_from_directory(os.path.join(baseD, rel_dir), filename)

    
    try:
        items = os.listdir(real_curDir)
    except PermissionError:
        flask.flash("Permission denied")
        return flask.redirect(flask.request.referrer or flask.url_for('fileManager_root'))

    l = curDir.split("/")
    location = ""
    for i in range(len(l)-1,-1,-1):
        if l[i] == "shared":
            break
        else:
            location = l[i] + "/" + location
    if location != "./":
        location = "./"+location

    
    files = {}
    if safe_subpath and safe_subpath != ".":
        parent = os.path.dirname(safe_subpath)
        files["../"] = {
            "href": "",
            "is_dir": True,
            "size": "",
            "filepath": f"/shared/{parent}" if parent else "/shared"
        }

    hiddenFiles = ['lastupdated.txt']
    for name in items:
        if name in hiddenFiles:
            continue
        path = os.path.join(real_curDir, name)
        files[name] = {
            "href": path,
            "is_dir": os.path.isdir(path),
            "size": f"  ({os.path.getsize(path)} bytes)" if os.path.isfile(path) else '/',
            "filepath": f"/shared/{os.path.join(safe_subpath, name)}"
        }

    cwd_for_template = "" if safe_subpath in ("", ".") else safe_subpath

    
    messages = flask.get_flashed_messages()
    alert_script = ""
    if messages:
        alert_script = "<script>" + "".join([f"alert('{m}');" for m in messages]) + "</script>"

    return flask.render_template(
        "fileManager.html",
        user=str(flask.session.get('username')).upper(),
        location=location,
        files=files,
        last_updated_info="DD/MM/YY by USER",
        global_html=flask.current_app.config.get('global_html'),
        cwd=cwd_for_template,
        alert_script=alert_script
    )

def handle_upload():
    if flask.session.get('authenticated') != True:
        return flask.redirect('/login')

    cwd = flask.request.form.get('cwd', "").strip()
    safe_subpath = os.path.normpath(cwd) if cwd else ""

    if safe_subpath and (safe_subpath.startswith("..") or os.path.isabs(safe_subpath)):
        flask.flash("Invalid path")
        return flask.redirect(flask.request.referrer or flask.url_for('fileManager_root'))

    target_base = os.path.join(baseD, safe_subpath)
    real_target_base = os.path.realpath(target_base)
    if not os.path.commonpath([real_target_base, os.path.realpath(baseD)]) == os.path.realpath(baseD):
        flask.flash("Invalid path")
        return flask.redirect(flask.request.referrer or flask.url_for('fileManager_root'))

    os.makedirs(real_target_base, exist_ok=True)

    files = flask.request.files.getlist('files')
    if not files:
        flask.flash("No files uploaded")
        return flask.redirect(flask.request.referrer or flask.url_for('fileManager_root'))

    for f in files:
        filename = f.filename
        safe_name = secure_filename(os.path.basename(filename))
        relative_path = os.path.dirname(filename)

        
        if relative_path:
            parts = [secure_filename(p) for p in relative_path.split(os.sep) if p and p != "."]
            relative_path_clean = os.path.join(*parts) if parts else ""
        else:
            relative_path_clean = ""

        
        disallowed_folders = ['upload','delete','shared']
        if any((p.lower() in disallowed_folders) for p in relative_path_clean.split(os.sep)):
            flask.flash("Folder name 'upload' is not allowed.")
            return flask.redirect(flask.request.referrer or flask.url_for('fileManager_root'))

        
        target_dir = os.path.join(real_target_base, relative_path_clean) if relative_path_clean else real_target_base
        os.makedirs(target_dir, exist_ok=True)

        
        if not safe_name:
            continue

        
        save_path = os.path.join(target_dir, safe_name)

       
        if os.path.isdir(save_path):
            flask.flash(f"A folder named '{safe_name}' already exists.")
            return flask.redirect(flask.request.referrer or flask.url_for('fileManager_root'))

        
        if os.path.exists(save_path) and os.path.isfile(save_path):
            os.remove(save_path)

        f.save(save_path)

    
    redirect_path = f"/shared/{safe_subpath}" if safe_subpath else "/shared"
    flask.flash("Upload completed successfully.")
    return flask.redirect(redirect_path)

def handle_delete():
    if flask.session.get('authenticated') != True:
        return flask.redirect('/login')

    target = flask.request.form.get('target', '').strip()
    safe_subpath = os.path.normpath(target)

    
    if safe_subpath.startswith("..") or os.path.isabs(safe_subpath):
        flask.flash("Invalid path")
        return flask.redirect(flask.request.referrer or flask.url_for('fileManager_root'))

    abs_path = os.path.join(baseD, safe_subpath)
    real_abs_path = os.path.realpath(abs_path)
    real_base = os.path.realpath(baseD)

    if not os.path.commonpath([real_abs_path, real_base]) == real_base:
        flask.flash("Invalid path")
        return flask.redirect(flask.request.referrer or flask.url_for('fileManager_root'))

    if not os.path.exists(real_abs_path):
        flask.flash("File or folder not found")
        return flask.redirect(flask.request.referrer or flask.url_for('fileManager_root'))

    try:
        if os.path.isdir(real_abs_path):
            os.rmdir(real_abs_path)
        else:
            os.remove(real_abs_path)
    except OSError:
        flask.flash("Cannot delete (folder not empty or permission denied)")
        return flask.redirect(flask.request.referrer or flask.url_for('fileManager_root'))

    flask.flash("Deleted successfully.")
    
    parent = os.path.dirname(safe_subpath)
    redirect_path = f"/shared/{parent}" if parent else "/shared"
    return flask.redirect(redirect_path)

def register_fileManager_routes(app):
    app.add_url_rule('/shared', 'fileManager_root', fileManager)
    app.add_url_rule('/shared/<path:subpath>', 'fileManager_sub', fileManager)
    app.add_url_rule('/shared/upload', 'file_upload', handle_upload, methods=['POST'])
    app.add_url_rule('/shared/delete', 'file_delete', handle_delete, methods=['POST'])
