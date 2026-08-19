// Copyright (C) 2020-2022 Intel Corporation
// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import React from 'react';
import { Link } from 'react-router-dom';
import { Row, Col } from 'antd/lib/grid';
import Card from 'antd/lib/card';
import Empty from 'antd/lib/empty';
import Text from 'antd/lib/typography/Text';
import { Task } from 'cvat-core-wrapper';

interface Props {
    task: Task;
}

export default function JobListComponent(props: Readonly<Props>): JSX.Element {
    const { task } = props;

    return (
        <div className='cvat-jobs-list-wrapper'>
            <Row>
                <Col>
                    <Text className='cvat-text-color cvat-jobs-header'>图片标注</Text>
                </Col>
            </Row>
            {task.jobs.length ? (
                <div className='cvat-task-job-list'>
                    <Col className='cvat-jobs-list'>
                        {task.jobs.map((job) => (
                            <Card className='cvat-job-item' key={job.id}>
                                <Row justify='space-between' align='middle'>
                                    <Col>
                                        <Text>{`共 ${job.frameCount} 张图片`}</Text>
                                    </Col>
                                    <Col>
                                        <Link to={`/tasks/${job.taskId}/jobs/${job.id}`}>开始标注</Link>
                                    </Col>
                                </Row>
                            </Card>
                        ))}
                    </Col>
                </div>
            ) : (
                <Empty description='暂无可标注图片' />
            )}
        </div>
    );
}
