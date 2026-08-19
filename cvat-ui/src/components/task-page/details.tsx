// Copyright (C) 2019-2022 Intel Corporation
// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import React, { useEffect, useState } from 'react';
import dayjs from 'dayjs';

import { Row, Col } from 'antd/lib/grid';
import Text from 'antd/lib/typography/Text';
import Title from 'antd/lib/typography/Title';

import { getCore, Task } from 'cvat-core-wrapper';
import Preview from 'components/common/preview';
import LabelsEditor from 'components/labels-editor/labels-editor';
import { getTaskReview } from 'utils/local-api';

interface Props {
    task: Task;
    onUpdateTask: (task: Task, fields?: Parameters<Task['save']>[0]) => Promise<Task>;
}

const core = getCore();

export default function DetailsComponent(props: Props): JSX.Element {
    const { task, onUpdateTask } = props;
    const [name, setName] = useState(task.name);
    const [categoriesLocked, setCategoriesLocked] = useState<boolean>();

    useEffect(() => {
        setName(task.name);
    }, [task.name]);

    useEffect(() => {
        let active = true;
        setCategoriesLocked(undefined);
        getTaskReview(task.id).then((summary) => {
            if (active) setCategoriesLocked(summary.reviewed > 0);
        }).catch(() => {
            if (active) setCategoriesLocked(true);
        });
        return () => {
            active = false;
        };
    }, [task.id]);

    const owner = task.owner?.username;
    const created = dayjs(task.createdDate).format('YYYY年M月D日');

    return (
        <div className='cvat-task-details'>
            <Row justify='start' align='middle'>
                <Col className='cvat-task-details-task-name'>
                    <Title
                        level={4}
                        editable={{
                            tooltip: '修改任务名称',
                            onChange: (value: string): void => {
                                setName(value);
                                task.name = value;
                                onUpdateTask(task);
                            },
                        }}
                        className='cvat-text-color cvat-task-name'
                    >
                        {name}
                    </Title>
                </Col>
            </Row>
            <Row justify='space-between' align='top'>
                <Col md={8} lg={7} xl={7} xxl={6}>
                    <Preview
                        task={task}
                        loadingClassName='cvat-task-item-loading-preview'
                        emptyPreviewClassName='cvat-task-item-empty-preview'
                        previewClassName='cvat-task-item-preview'
                    />
                </Col>
                <Col md={16} lg={17} xl={17} xxl={18}>
                    <Text type='secondary'>
                        {`任务 #${task.id} · 创建者 ${owner || '未知'} · 创建时间 ${created}`}
                    </Text>
                    <Row className='cvat-task-details-labels' style={{ marginTop: 16 }}>
                        <Col span={24}>
                            <Text className='cvat-text-color'>类别</Text>
                            {categoriesLocked && (
                                <Text type='secondary' style={{ marginLeft: 8 }}>
                                    已锁定类别编号和顺序，可继续新增或重命名
                                </Text>
                            )}
                            <LabelsEditor
                                labels={task.labels.map((label) => label.toJSON())}
                                enableSkeletonCreator={false}
                                enableFromModelCreator={false}
                                enableRawEditor={false}
                                showLabelType={false}
                                showAttributes={false}
                                allowDelete={categoriesLocked === false}
                                onSubmit={(labels): Promise<Task> => onUpdateTask(task, {
                                    labels: labels.map((labelData): any => new core.classes.Label(labelData)),
                                })}
                            />
                        </Col>
                    </Row>
                </Col>
            </Row>
        </div>
    );
}
