// Copyright (C) 2020-2022 Intel Corporation
// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import React from 'react';
import { useSelector } from 'react-redux';
import { useHistory } from 'react-router';
import Button from 'antd/lib/button';
import Icon from '@ant-design/icons';

import { MainMenuIcon } from 'icons';
import { Job } from 'cvat-core-wrapper';
import { CombinedState } from 'reducers';

interface Props {
    removeAnnotationsConfirmComponent?: React.ComponentType<any>;
}

export default function AnnotationMenuComponent(_props: Props): JSX.Element {
    const history = useHistory();
    const job = useSelector((state: CombinedState) => state.annotation.job.instance as Job);

    return (
        <Button
            type='link'
            className='cvat-annotation-header-menu-button cvat-annotation-header-button'
            onClick={() => history.push(`/tasks/${job.taskId}`)}
        >
            <Icon component={MainMenuIcon} />
            返回任务
        </Button>
    );
}
