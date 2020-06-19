#!/usr/bin/env python
# -*- coding:utf-8 -*-

import hashlib
import json
import os
import pathlib
import re
import shutil
import tempfile
import urllib.request
import zipfile
from os.path import join

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from special_escape import generate_printer, generate_encoder

encoder = generate_encoder("eu4", "txt")
printer = generate_printer("eu4", "txt")

_ = join

"""
$ 階級について
こちら参照のこと：https://gist.github.com/matanki-saito/a2afb80eeeef612a28426af31e226d3d
"""
replace_estate_parameter_map_definition = {
    "GetNobilityName": "Get貴族Name",
    "GetClergyName": "Get聖職者Name",
    "GetBurghersName": "Get市民Name",

    "GetCossacksName": "GetコサックName",
    "GetDhimmiName": "GetズィンミーName",
    "GetTribesName": "Get部族Name",

    "GetBrahminsName": "GetバラモンName",
    "GetJainsName": "Getジャイナ教徒Name",
    "GetMarathasName": "GetマラーターName",
    "GetRajputsName": "GetラージプートName",
    "GetVaishyasName": "GetヴァイシャName"
}


def upload_mod_to_google_drive(upload_file_path,
                               name,
                               folder_id):
    """
    GoogleDriveにファイルをアップロードする
    :param upload_file_path:
    :param name:
    :param folder_id:
    :return: CDNのURL
    """

    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()

    # Create GoogleDrive instance with authenticated GoogleAuth instance.
    drive = GoogleDrive(gauth)

    file1 = drive.CreateFile({
        'title': name,
        'parents': [
            {
                "kind": "drive#fileLink",
                "id": folder_id
            }
        ]
    })
    file1.SetContentFile(upload_file_path)
    file1.Upload()

    file1.InsertPermission({
        'type': 'anyone',
        'value': 'anyone',
        'role': 'reader'})

    file1.FetchMetadata()

    return "{}/{}?key={}&alt=media".format("https://www.googleapis.com/drive/v3/files",
                                           file1['id'],
                                           "AIzaSyAAt1kNBcu9uiPWPIxAcR0gZefmWHcjjpM")


def download_trans_zip_from_paratranz(project_id,
                                      secret,
                                      out_file_path,
                                      base_url="https://paratranz.cn"):
    """
    paratranzからzipをダウンロードする
    :param project_id:
    :param secret:
    :param base_url:
    :param out_file_path:
    :return:
    """

    request_url = "{}/api/projects/{}/artifacts/download".format(base_url, project_id)
    req = urllib.request.Request(request_url)
    req.add_header("Authorization", secret)

    with open(out_file_path, "wb") as my_file:
        my_file.write(urllib.request.urlopen(req).read())

    return out_file_path


def assembly_app_mod_zip_file(resource_image_file_path,
                              source_dir_path,
                              out_directory_path):
    """
    Appモッドを作成
    :param source_dir_path:
    :param resource_image_file_path: 画像ファイルパス
    :param out_directory_path: 出力ファイルパス
    :return:
    """

    with tempfile.TemporaryDirectory() as temp_dir_path:
        # 画像ファイル
        shutil.copy(resource_image_file_path, temp_dir_path)

        shutil.copytree(source_dir_path, _(temp_dir_path, 'localisation'))

        # zip化する
        return shutil.make_archive(_(out_directory_path, 'mod'), 'zip', root_dir=temp_dir_path)


def replace_estate_parameters(replace_estate_parameter_map,
                              source_dir_path,
                              output_dir_path):
    """
    特殊なパラメータを置き換える
    :param replace_estate_parameter_map:
    :param source_dir_path:
    :param output_dir_path:
    :return:
    """

    shutil.rmtree(output_dir_path, ignore_errors=True)
    os.makedirs(output_dir_path, exist_ok=True)

    match_pattern = re.compile("{}".format(
        r"|".join(replace_estate_parameter_map.keys())
    ))

    def repl(match_obj):
        return replace_estate_parameter_map.get(match_obj.group(0))

    for source_file_path in pathlib.Path(source_dir_path).glob('**/*.yml'):
        with open(str(source_file_path), 'rt', encoding='utf_8_sig', errors='ignore', newline='') as f:
            replaced_source_file_text = re.sub(match_pattern, repl, f.read())
            write_file_path = str(_(output_dir_path, source_file_path.name))
            with open(write_file_path, 'wt', encoding='utf_8_sig') as w:
                w.write(replaced_source_file_text)


def salvage_files_from_paratranz_trans_zip(out_dir_path,
                                           paratranz_zip_path,
                                           folder_list,
                                           head_folder_name):
    shutil.rmtree(out_dir_path, ignore_errors=True)

    with zipfile.ZipFile(paratranz_zip_path) as paratranz_zip:
        special_files = filter(lambda name: name.startswith(head_folder_name + "/"), paratranz_zip.namelist())

        with tempfile.TemporaryDirectory() as temp_dir_path:
            paratranz_zip.extractall(path=temp_dir_path, members=special_files)

            for folder in folder_list:
                shutil.copytree(_(temp_dir_path, head_folder_name, folder), out_dir_path)


def generate_dot_mod_file(mod_title_name,
                          mod_file_name,
                          mod_tags,
                          mod_image_file_path,
                          mod_supported_version,
                          out_dir_path):
    """
    .modファイルを作る
    :param mod_title_name:
    :param mod_file_name: zipファイルの名前（.zipを含まない）
    :param mod_tags: Set<String>型
    :param mod_image_file_path:
    :param mod_supported_version:
    :param out_dir_path: 出力ディレクトリのパス
    :return: 出力ファイルパス
    """

    os.makedirs(out_dir_path, exist_ok=True)

    out_file_path = _(out_dir_path, "{}.mod".format(mod_file_name))

    with open(out_file_path, "w", encoding="utf-8") as fw:
        lines = [
            'name="{}"'.format(mod_title_name),
            'archive="mod/{}.zip"'.format(mod_file_name),
            'tags={}'.format("{" + " ".join(map(lambda c: '"{}"'.format(c), mod_tags)) + "}"),
            'supported_version="{}"'.format(mod_supported_version),
            'picture="{}"'.format(mod_image_file_path)
        ]

        fw.write("\n".join(lines))

    return out_file_path


def generate_distribution_file(url,
                               mod_file_path,
                               out_file_path):
    """
    trielaで使用する配布用設定ファイルを作成する。
    :param url:
    :param mod_file_path:
    :param out_file_path:
    :return:
    """

    with open(mod_file_path, 'rb') as fr:
        md5 = hashlib.md5(fr.read()).hexdigest()

    d_new = {'file_md5': md5,
             'url': url,
             'file_size': os.path.getsize(mod_file_path)}

    with open(out_file_path, "w", encoding="utf-8") as fw:
        json.dump(d_new, fw, indent=2, ensure_ascii=False)


def pack_mod(out_file_path,
             mod_zip_path,
             mod_title_name,
             mod_file_name,
             mod_tags,
             mod_supported_version,
             mod_image_file_path):
    with tempfile.TemporaryDirectory() as temp_dir_path:
        # .modファイルを作成する
        generate_dot_mod_file(
            mod_title_name=mod_title_name,
            mod_file_name=mod_file_name,
            mod_tags=mod_tags,
            mod_image_file_path=mod_image_file_path,
            mod_supported_version=mod_supported_version,
            out_dir_path=temp_dir_path)

        # zipをコピー
        shutil.copy(mod_zip_path, _(temp_dir_path, "{}.zip".format(mod_file_name)))

        return shutil.make_archive(out_file_path, 'zip', root_dir=temp_dir_path)


def special_escape(source_dir_path, output_dir_path):
    shutil.rmtree(output_dir_path, ignore_errors=True)
    os.makedirs(output_dir_path, exist_ok=True)

    for source_file_path in pathlib.Path(source_dir_path).glob('**/*.yml'):
        printer(src_array=encoder(src_array=map(ord, source_file_path.read_text(
            encoding="utf-8"
        ))), out_file_path=_(output_dir_path, source_file_path.name))


def main():
    # 一時フォルダ用意
    tmp_directory_path = _(".", "tmp")
    os.makedirs(tmp_directory_path, exist_ok=True)

    # 出力フォルダ用意
    os.makedirs(_(".", "out"), exist_ok=True)

    # 翻訳の最新版をダウンロードする
    p_file_path = _(".", "tmp", "paratranz.zip")
    if not os.path.exists(p_file_path):
        download_trans_zip_from_paratranz(
            project_id=76,
            secret=os.environ.get("PARATRANZ_SECRET"),
            out_file_path=p_file_path)

    print("p_file_path:{}".format(p_file_path))

    # utf8ファイルを抽出する（この後git pushするのにも使う）
    localisation_dir_path = _(tmp_directory_path, "source", "localisation")
    salvage_files_from_paratranz_trans_zip(out_dir_path=localisation_dir_path,
                                           folder_list=["localisation"],
                                           paratranz_zip_path=p_file_path,
                                           head_folder_name="utf8")

    print("Finish extracting localisation dir")

    # 特殊なキーワードを置き換える
    replaced_localization_dir_path = _(tmp_directory_path, "replaced_localization")
    replace_estate_parameters(replace_estate_parameter_map=replace_estate_parameter_map_definition,
                              source_dir_path=localisation_dir_path,
                              output_dir_path=replaced_localization_dir_path)

    print("Finish replacing special keywords")

    # 特殊エンコードする
    special_escaped_localization = _(tmp_directory_path, "special_escaped_localization")
    special_escape(source_dir_path=replaced_localization_dir_path,
                   output_dir_path=special_escaped_localization)

    print("Finish special encoding")

    # AppModを構築する
    app_mod_zip_file_path = assembly_app_mod_zip_file(
        source_dir_path=special_escaped_localization,
        resource_image_file_path=_(".", "resource", "title.jpg"),
        out_directory_path=tmp_directory_path)

    print("app_mod_zip_file_path:{}".format(app_mod_zip_file_path))

    # packする
    mod_pack_file_path = pack_mod(
        out_file_path=_(".", "out", "eu4_ap1_mod"),
        mod_file_name="jpmod_ap1_mod",
        mod_zip_path=app_mod_zip_file_path,
        mod_title_name="JPMOD Main 2: Text",
        mod_tags={"Translation", "Localisation"},
        mod_image_file_path="title.jpg",
        mod_supported_version="1.30.*.*")

    print("mod_pack_file_path:{}".format(mod_pack_file_path))

    # GoogleDriveにアップロード from datetime import datetime as dt
    from datetime import datetime as dt

    cdn_url = upload_mod_to_google_drive(
        upload_file_path=mod_pack_file_path,
        name=dt.now().strftime('%Y-%m-%d_%H-%M-%S-{}.zip'.format("eu4-ap1")),
        folder_id='1MUdH6S6O-M_Y5jRUzNrzQ8tPZOhm_aES')

    print("cdn_url:{}".format(cdn_url))

    # distributionファイルを生成する
    generate_distribution_file(url=cdn_url,
                               out_file_path=_(".", "out", "dist.v2.json"),
                               mod_file_path=mod_pack_file_path)

    # git pushするために移動する
    shutil.copytree("./", )


if __name__ == "__main__":
    main()
