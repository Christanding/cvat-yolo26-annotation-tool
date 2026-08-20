// SPDX-License-Identifier: MIT

import './styles.scss';
import React, { useEffect, useState } from 'react';
import Alert from 'antd/lib/alert';
import Button from 'antd/lib/button';
import Card from 'antd/lib/card';
import Col from 'antd/lib/col';
import Descriptions from 'antd/lib/descriptions';
import Form from 'antd/lib/form';
import InputNumber from 'antd/lib/input-number';
import Modal from 'antd/lib/modal';
import Progress from 'antd/lib/progress';
import Radio from 'antd/lib/radio';
import Row from 'antd/lib/row';
import Select from 'antd/lib/select';
import Text from 'antd/lib/typography/Text';
import notification from 'antd/lib/notification';
import { SyncOutlined } from '@ant-design/icons';

import {
    appendTaskImages,
    AppendableTask,
    createExtraction,
    ExtractionParameters,
    ExtractionResult,
    getExtraction,
    listVideos,
    listAppendableTasks,
    LocalAPIError,
    VideoMetadata,
} from 'utils/local-api';

type Strength = ExtractionParameters['strength'];

export default function VideoExtractionPage(): JSX.Element {
    const [videos, setVideos] = useState<VideoMetadata[]>([]);
    const [selectedPath, setSelectedPath] = useState<string>();
    const [startTime, setStartTime] = useState(0);
    const [endTime, setEndTime] = useState(0);
    const [interval, setInterval] = useState(1);
    const [strength, setStrength] = useState<Strength>('medium');
    const [loadingVideos, setLoadingVideos] = useState(false);
    const [jobId, setJobId] = useState<string>();
    const [progress, setProgress] = useState(0);
    const [result, setResult] = useState<ExtractionResult>();
    const [tasks, setTasks] = useState<AppendableTask[]>([]);
    const [selectedTaskID, setSelectedTaskID] = useState<number>();
    const [loadingTasks, setLoadingTasks] = useState(false);
    const [addingImages, setAddingImages] = useState(false);

    const selectedVideo = videos.find((video) => video.path === selectedPath);

    const refreshVideos = async (): Promise<void> => {
        setLoadingVideos(true);
        try {
            const items = await listVideos();
            setVideos(items);
            if (selectedPath && !items.some((item) => item.path === selectedPath)) {
                setSelectedPath(undefined);
            }
        } catch (error: any) {
            notification.error({
                message: '无法读取视频目录',
                description: error.message,
            });
        } finally {
            setLoadingVideos(false);
        }
    };

    const refreshTasks = async (): Promise<void> => {
        setLoadingTasks(true);
        try {
            const items = await listAppendableTasks();
            setTasks(items);
            if (selectedTaskID && !items.some((item) => item.id === selectedTaskID)) {
                setSelectedTaskID(undefined);
            }
        } catch (error: any) {
            notification.error({ message: '无法读取任务列表', description: error.message });
        } finally {
            setLoadingTasks(false);
        }
    };

    useEffect(() => {
        refreshVideos();
        refreshTasks();
    }, []);

    useEffect(() => {
        if (!jobId) return undefined;
        let stopped = false;
        let timer: number | undefined;

        const poll = async (): Promise<void> => {
            try {
                const status = await getExtraction(jobId);
                if (stopped) return;
                setProgress(status.progress);
                if (status.status === 'finished' && status.result) {
                    setResult(status.result);
                    setJobId(undefined);
                    refreshTasks();
                    notification.success({ message: '视频抽帧完成' });
                } else if (status.status === 'failed') {
                    setJobId(undefined);
                    notification.error({
                        message: '视频抽帧失败',
                        description: status.error,
                    });
                } else {
                    timer = window.setTimeout(poll, 1000);
                }
            } catch (error: any) {
                if (!stopped) {
                    setJobId(undefined);
                    notification.error({ message: '无法获取抽帧进度', description: error.message });
                }
            }
        };

        poll();
        return () => {
            stopped = true;
            if (timer) window.clearTimeout(timer);
        };
    }, [jobId]);

    const startExtraction = async (overwrite = false): Promise<void> => {
        if (!selectedPath) {
            notification.warning({ message: '请先选择视频' });
            return;
        }
        if (endTime < startTime) {
            notification.warning({ message: '结束时间不能早于开始时间' });
            return;
        }

        setResult(undefined);
        setProgress(0);
        try {
            const job = await createExtraction({
                path: selectedPath,
                start_time: startTime,
                end_time: endTime,
                interval,
                strength,
                overwrite,
            });
            setJobId(job.id);
        } catch (error: any) {
            if (error instanceof LocalAPIError && error.code === 'output_exists') {
                Modal.confirm({
                    title: '抽帧目录已存在',
                    content: '覆盖后，现有抽帧图片将被新的结果替换。原视频不会被修改。',
                    okText: '覆盖并重新抽帧',
                    cancelText: '取消',
                    onOk: () => startExtraction(true),
                });
            } else {
                notification.error({ message: '无法开始抽帧', description: error.message });
            }
        }
    };

    const addImagesToTask = async (): Promise<void> => {
        if (!result || !selectedTaskID) {
            notification.warning({ message: '请先选择要加入的任务' });
            return;
        }
        setAddingImages(true);
        try {
            const appendResult = await appendTaskImages(selectedTaskID, result.output_path);
            const task = tasks.find((item) => item.id === selectedTaskID);
            notification.success({
                message: '图片已加入任务',
                description: (
                    `已向“${task?.name || `任务 #${selectedTaskID}`}”添加 ` +
                    `${appendResult.added_count} 张图片，任务现有 ${appendResult.total_count} 张图片。`
                ),
            });
            await refreshTasks();
        } catch (error: any) {
            notification.error({ message: '无法添加图片', description: error.message });
        } finally {
            setAddingImages(false);
        }
    };

    return (
        <Row justify='center' align='top' className='cvat-video-extraction-page'>
            <Col md={20} lg={16} xl={14} xxl={12}>
                <Text className='cvat-title'>视频抽帧</Text>
                <Card>
                    <Form layout='vertical'>
                        <Form.Item label='视频' required>
                            <Row gutter={8} wrap={false}>
                                <Col flex='auto'>
                                    <Select
                                        showSearch
                                        loading={loadingVideos}
                                        value={selectedPath}
                                        placeholder='选择工作区内的 MP4 或 MOV 视频'
                                        options={videos.map((video) => ({
                                            value: video.path,
                                            label: video.path,
                                        }))}
                                        onChange={(path: string) => {
                                            const video = videos.find((item) => item.path === path);
                                            setSelectedPath(path);
                                            setStartTime(0);
                                            setEndTime(video?.duration || 0);
                                            setResult(undefined);
                                        }}
                                    />
                                </Col>
                                <Col>
                                    <Button
                                        icon={<SyncOutlined />}
                                        loading={loadingVideos}
                                        onClick={refreshVideos}
                                    >
                                        刷新目录
                                    </Button>
                                </Col>
                            </Row>
                        </Form.Item>

                        {selectedVideo ? (
                            <Alert
                                type='info'
                                showIcon
                                message={(
                                    `时长 ${selectedVideo.duration} 秒，` +
                                    `${selectedVideo.width}×${selectedVideo.height}，` +
                                    `${selectedVideo.fps.toFixed(2)} fps`
                                )}
                            />
                        ) : null}

                        <Row gutter={16}>
                            <Col span={8}>
                                <Form.Item label='开始时间（秒）'>
                                    <InputNumber
                                        min={0}
                                        precision={0}
                                        value={startTime}
                                        onChange={(value) => setStartTime(value || 0)}
                                    />
                                </Form.Item>
                            </Col>
                            <Col span={8}>
                                <Form.Item label='结束时间（秒）'>
                                    <InputNumber
                                        min={0}
                                        precision={0}
                                        value={endTime}
                                        onChange={(value) => setEndTime(value || 0)}
                                    />
                                </Form.Item>
                            </Col>
                            <Col span={8}>
                                <Form.Item label='抽帧间隔（秒）'>
                                    <InputNumber
                                        min={1}
                                        precision={0}
                                        value={interval}
                                        onChange={(value) => setInterval(value || 1)}
                                    />
                                </Form.Item>
                            </Col>
                        </Row>

                        <Form.Item label='连续帧去重强度'>
                            <Radio.Group
                                value={strength}
                                optionType='button'
                                buttonStyle='solid'
                                onChange={(event) => setStrength(event.target.value)}
                                options={[
                                    { label: '低', value: 'low' },
                                    { label: '中', value: 'medium' },
                                    { label: '高', value: 'high' },
                                ]}
                            />
                        </Form.Item>

                        <Button
                            type='primary'
                            loading={!!jobId}
                            disabled={!selectedPath}
                            onClick={() => startExtraction()}
                        >
                            开始抽帧
                        </Button>
                    </Form>

                    {jobId ? <Progress percent={progress} status='active' /> : null}
                    {result ? (
                        <>
                            <Descriptions title='抽帧结果' bordered column={2}>
                                <Descriptions.Item label='原始抽取数量'>{result.source_count}</Descriptions.Item>
                                <Descriptions.Item label='完全重复数量'>{result.exact_duplicates}</Descriptions.Item>
                                <Descriptions.Item label='相似帧跳过数量'>{result.similar_skipped}</Descriptions.Item>
                                <Descriptions.Item label='最终保留数量'>{result.kept_count}</Descriptions.Item>
                                <Descriptions.Item label='输出目录' span={2}>{result.output_path}</Descriptions.Item>
                            </Descriptions>
                            <Form layout='vertical' className='cvat-video-extraction-append-form'>
                                <Form.Item
                                    label='加入已有任务'
                                    extra='新加入的图片状态为“未检查”，任务类别及已有标注保持不变。'
                                >
                                    <Row gutter={8} wrap={false}>
                                        <Col flex='auto'>
                                            <Select
                                                showSearch
                                                optionFilterProp='label'
                                                loading={loadingTasks}
                                                value={selectedTaskID}
                                                placeholder='选择本地工作区图片任务'
                                                options={tasks.map((task) => ({
                                                    value: task.id,
                                                    label: `${task.name}（${task.size} 张）`,
                                                }))}
                                                onChange={setSelectedTaskID}
                                                notFoundContent='没有可追加图片的任务'
                                            />
                                        </Col>
                                        <Col>
                                            <Button
                                                type='primary'
                                                loading={addingImages}
                                                disabled={!selectedTaskID}
                                                onClick={addImagesToTask}
                                            >
                                                添加图片
                                            </Button>
                                        </Col>
                                    </Row>
                                </Form.Item>
                            </Form>
                        </>
                    ) : null}
                </Card>
            </Col>
        </Row>
    );
}
