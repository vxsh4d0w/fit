#!/usr/bin/env python3
# -*- coding:utf-8 -*-
######
# -----
# Copyright (c) 2023 FIT-Project
# SPDX-License-Identifier: GPL-3.0-only
# -----
######

from model.db import Db
from sqlalchemy import Column, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Option(Base):
    __tablename__ = 'configuration_option'
    id = Column(Integer, primary_key=True)
    whois = Column(Boolean)
    headers = Column(Boolean)
    traceroute = Column(Boolean)
    SSLkeylog = Column(Boolean)
    Nslookup = Column(Boolean)
    SSLcertificate = Column(Boolean)


    def __init__(self) -> None:
        super().__init__()
        self.db = Db()
        self.metadata.create_all(self.db.engine)

    def get(self):
        if self.db.session.query(Option).first() is None:
            self.set_default_values()

        return self.db.session.query(Option).all()

    def update(self, configuration):
        self.db.session.query(Option).filter(Option.id == configuration.get('id')).update(configuration)
        self.db.session.commit()

    def set_default_values(self):

        self.db.session.add(self)
        self.db.session.commit()

