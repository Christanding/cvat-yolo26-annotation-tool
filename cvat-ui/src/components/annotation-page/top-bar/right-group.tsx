// Copyright (C) 2020-2022 Intel Corporation
// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import React from 'react';
import { Col } from 'antd/lib/grid';
import Icon from '@ant-design/icons';
import Button from 'antd/lib/button';

import { FullscreenIcon } from 'icons';
import { Job } from 'cvat-core-wrapper';
import { Workspace } from 'reducers';

interface Props {
    showStatistics(): void;
    showFilters(): void;
    changeWorkspace(workspace: Workspace): void;
    jobInstance: Job;
    workspace: Workspace;
    annotationFilters: object[];
    initialOpenGuide: boolean;
}

export default function RightGroup(_props: Props): JSX.Element {
    return (
        <Col className='cvat-annotation-header-right-group'>
            <Button
                type='link'
                className='cvat-annotation-header-fullscreen-button cvat-annotation-header-button'
                onClick={(): void => {
                    if (window.document.fullscreenEnabled) {
                        if (window.document.fullscreenElement) window.document.exitFullscreen();
                        else window.document.documentElement.requestFullscreen();
                    }
                }}
            >
                <Icon component={FullscreenIcon} />
                全屏
            </Button>
        </Col>
    );
}
