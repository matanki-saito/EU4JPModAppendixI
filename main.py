#!/usr/bin/env python
# -*- coding:utf-8 -*-

import hashlib
import json
import os
import shutil
import tempfile
import urllib.request
import zipfile
from os.path import join

from boto3.session import Session

_ = join


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
                              resource_paratranz_trans_zip_file_path,
                              out_file_path):
    """
    Appモッドを作成
    :param resource_paratranz_trans_zip_file_path: Paratranzからダウンロードできるzipファイルのパス
    :param resource_image_file_path: 画像ファイルパス
    :param out_file_path: 出力ファイルパス
    :return:
    """

    with tempfile.TemporaryDirectory() as temp_dir_path:
        # 画像ファイル
        shutil.copy(resource_image_file_path, temp_dir_path)

        # localisation
        salvage_files_from_paratranz_trans_zip(out_dir_path=_(temp_dir_path, "localisation"),
                                               folder_list=["localisation"],
                                               paratranz_zip_path=resource_paratranz_trans_zip_file_path,
                                               head_folder_name="special")

        # zip化する
        return shutil.make_archive(out_file_path, 'zip', root_dir=temp_dir_path)


def update_source(resource_paratranz_trans_zip_file_path):
    shutil.rmtree("source", ignore_errors=True)
    os.makedirs("source", exist_ok=True)

    salvage_files_from_paratranz_trans_zip(out_dir_path=_("source", "localisation"),
                                           folder_list=["localisation"],
                                           paratranz_zip_path=resource_paratranz_trans_zip_file_path,
                                           head_folder_name="utf8")


def salvage_files_from_paratranz_trans_zip(out_dir_path,
                                           paratranz_zip_path,
                                           folder_list,
                                           head_folder_name):
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


def upload_mod_to_s3(upload_file_path,
                     name,
                     bucket_name,
                     access_key,
                     secret_access_key,
                     region):
    """
    S3にファイルをアップロードする
    :param upload_file_path:
    :param name:
    :param bucket_name:
    :param access_key:
    :param secret_access_key:
    :param region:
    :return: CDNのURL
    """
    session = Session(aws_access_key_id=access_key,
                      aws_secret_access_key=secret_access_key,
                      region_name=region)

    s3 = session.resource('s3')
    s3.Bucket(bucket_name).upload_file(upload_file_path, name)

    return "{}/{}".format("https://d3fxmsw7mhzbqi.cloudfront.net", name)


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


def main():
    # 一時フォルダ用意
    os.makedirs(_(".", "tmp"), exist_ok=True)
    os.makedirs(_(".", "out"), exist_ok=True)

    # 翻訳の最新版をダウンロードする
    p_file_path = download_trans_zip_from_paratranz(
        project_id=76,
        secret=os.environ.get("PARATRANZ_SECRET"),
        out_file_path=_(".", "tmp", "paratranz.zip"))

    print("p_file_path:{}".format(p_file_path))

    # AppModを構築する
    app_mod_zip_file_path = assembly_app_mod_zip_file(
        resource_paratranz_trans_zip_file_path=p_file_path,
        resource_image_file_path=_(".", "resource", "title.jpg"),
        out_file_path=_(".", "tmp", "mod"))

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

    # S3にアップロード from datetime import datetime as dt
    from datetime import datetime as dt
    cdn_url = upload_mod_to_s3(
        upload_file_path=mod_pack_file_path,
        name=dt.now().strftime('%Y-%m-%d_%H-%M-%S-{}.zip'.format("eu4-ap1")),
        bucket_name="triela-file",
        access_key=os.environ.get("AWS_S3_ACCESS_KEY"),
        secret_access_key=os.environ.get("AWS_S3_SECRET_ACCESS_KEY"),
        region="ap-northeast-1")

    print("cdn_url:{}".format(cdn_url))

    # distributionファイルを生成する
    generate_distribution_file(url=cdn_url,
                               out_file_path=_(".", "out", "dist.v2.json"),
                               mod_file_path=mod_pack_file_path)

    # utf8ファイルを移動する（この後git pushする）
    update_source(resource_paratranz_trans_zip_file_path=p_file_path)


if __name__ == "__main__":
    main()
