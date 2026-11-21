import type { Hostel } from "../types/hostel"

export const areas = ['Amamoma', 'Kwaprow', 'Apewosika', 'Ayensu']
export const roomTypes = ['Single', 'Double', 'Triple', 'Quad']
export const lifestyles = ['Quiet', 'Clean', 'Studious', 'Social', 'Early riser', 'Non-smoker']
export const levels = ['100', '200', '300', '400']
export const money = (value: number) => `GH₵ ${value.toLocaleString('en-GH')}`
export const dateLabel = (value: string) => new Intl.DateTimeFormat('en-GH', { dateStyle: 'medium' }).format(new Date(value))
export const beds = (hostel: Hostel) => hostel.rooms.reduce((sum, room) => sum + room.beds, 0)
export const price = (hostel: Hostel) => hostel.rooms.length ? Math.min(...hostel.rooms.map(room => room.price)) : null
